"""Tools that suggest a change. They check it would work and keep it for the person to confirm.

What the person agrees to is the summary written here from the records, not the model's words.
"""

from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from jalada.modules.agent.application.proposals import ActionProposals
from jalada.modules.agent.application.tools import Tool, ToolContext
from jalada.modules.agent.domain.proposals import ActionKind
from jalada.modules.ledger.application.entry_review import EntryReview
from jalada.modules.ledger.application.ledger import Ledger
from jalada.modules.ledger.domain.categories import CATEGORIES, Direction
from jalada.modules.ledger.domain.entries import Entry
from jalada.shared.errors import EntryNotFound

WAITS = "Suggested. It changes nothing until the person taps Confirm."


class PaymentArguments(BaseModel):
    id: UUID = Field(description="The payment's id, from waiting_to_check or search_payments.")


class SuggestConfirm(Tool[PaymentArguments]):
    name = "suggest_confirm"
    description = (
        "Suggest confirming a payment waiting on To check that is ready_to_confirm. "
        "The person confirms it with a tap; nothing changes before that."
    )
    arguments = PaymentArguments
    label = "Preparing a change for you"

    def __init__(self, review: EntryReview, proposals: ActionProposals) -> None:
        self._review = review
        self._proposals = proposals

    def run(self, context: ToolContext, arguments: PaymentArguments) -> dict[str, Any]:
        waiting = self._review.queue(context.user_id)
        item = next((i for i in waiting if i.entry and i.entry.id == arguments.id), None)
        if item is None or item.entry is None:
            return {"error": "That payment is not waiting on To check."}
        if not item.ready:
            return {
                "error": "That payment needs details checked on To check before it can be "
                "confirmed. Tell the person to open To check."
            }
        summary = f"Confirm {describe(item.entry)}"
        payload = {"entry_id": str(item.entry.id)}
        self._proposals.propose(context, ActionKind.CONFIRM_PAYMENT, payload, summary)
        return {"suggested": summary, "status": WAITS}


class CategoryArguments(BaseModel):
    id: UUID = Field(description="The payment's id, from search_payments or waiting_to_check.")
    category: str = Field(max_length=40, description="The new category's slug.")


class SuggestCategory(Tool[CategoryArguments]):
    name = "suggest_category"
    description = (
        "Suggest a different category for one payment. The person confirms it with a tap; "
        "nothing changes before that."
    )
    arguments = CategoryArguments
    label = "Preparing a change for you"

    def __init__(self, ledger: Ledger, proposals: ActionProposals) -> None:
        self._ledger = ledger
        self._proposals = proposals

    def run(self, context: ToolContext, arguments: CategoryArguments) -> dict[str, Any]:
        try:
            entry = self._ledger.detail(context.user_id, arguments.id).entry
        except EntryNotFound:
            return {"error": "There is no payment with that id."}
        category = CATEGORIES.get(arguments.category)
        fitting = {c.slug: c.name for c in CATEGORIES.values() if c.direction == entry.direction}
        if category is None or category.slug not in fitting:
            return {
                "error": f"{arguments.category!r} is not a category for this payment.",
                "categories": fitting,
            }
        if entry.category == category.slug:
            return {"error": f"The payment is already in {category.name}."}
        before = CATEGORIES[entry.category].name if entry.category in CATEGORIES else "none"
        summary = f"Move {describe(entry)} from {before} to {category.name}"
        payload = {"entry_id": str(entry.id), "category": category.slug}
        self._proposals.propose(context, ActionKind.CHANGE_CATEGORY, payload, summary)
        return {"suggested": summary, "status": WAITS}


def describe(entry: Entry) -> str:
    """A payment in a few words: Ksh 2,500.00 to KPLC PREPAID on 4 Jul 2026."""
    amount = f"Ksh {Decimal(entry.amount_cents or 0) / 100:,.2f}"
    side = "from" if entry.direction == Direction.IN else "to"
    who = f" {side} {entry.counterparty}" if entry.counterparty else ""
    day = f" on {entry.occurred_on.day} {entry.occurred_on:%b %Y}" if entry.occurred_on else ""
    return f"{amount}{who}{day}"
