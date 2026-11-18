from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from jalada.modules.agent.application.lookups.shapes import category_name, kes, payment
from jalada.modules.agent.application.tools import Tool, ToolContext
from jalada.modules.ledger.application.entry_review import EntryReview
from jalada.modules.ledger.application.ledger import Ledger
from jalada.modules.ledger.application.review_queue import ReviewItem
from jalada.shared.errors import EntryNotFound

# The queue is counted up to here; the person sees the rest on To check.
COUNTED = 100
SHOWN = 10


class NoArguments(BaseModel):
    pass


class WaitingToCheck(Tool[NoArguments]):
    name = "waiting_to_check"
    label = "Looking at To check"
    description = "What is waiting on the To check page, oldest first, and why."
    arguments = NoArguments

    def __init__(self, review: EntryReview) -> None:
        self._review = review

    def run(self, context: ToolContext, arguments: NoArguments) -> dict[str, Any]:
        queue = self._review.queue(context.user_id, COUNTED)
        return {
            "waiting": len(queue),
            "at_least": len(queue) == COUNTED,
            "first": [_item(item) for item in queue[:SHOWN]],
        }


class PaymentArguments(BaseModel):
    id: UUID = Field(description="A payment id from search_payments.")


class PaymentDetails(Tool[PaymentArguments]):
    name = "payment_details"
    label = "Opening the payment"
    description = "One payment with the evidence kept for it and what has been changed."
    arguments = PaymentArguments

    def __init__(self, ledger: Ledger) -> None:
        self._ledger = ledger

    def run(self, context: ToolContext, arguments: PaymentArguments) -> dict[str, Any]:
        try:
            detail = self._ledger.detail(context.user_id, arguments.id)
        except EntryNotFound:
            return {"error": "There is no payment with that id."}
        return {
            **payment(detail.entry),
            "mpesa_code": detail.entry.mpesa_code,
            "counted_on_a_certificate": detail.certificate_id is not None,
            "evidence": [
                {
                    "role": evidence.role,
                    "file_type": evidence.content_type,
                    "received": evidence.received_at.date().isoformat(),
                }
                for evidence in detail.evidence
            ],
            "history": [
                {
                    "date": item.at.date().isoformat(),
                    "by": item.actor,
                    "action": item.action,
                    "changed": list(item.changed),
                }
                for item in detail.history
            ],
        }


def _item(item: ReviewItem) -> dict[str, Any]:
    entry = item.entry
    shown: dict[str, Any] = {
        "why": _why(item),
        "evidence": item.evidence.kind,
        "received": item.evidence.received_at.date().isoformat(),
    }
    if entry is not None:
        shown |= {
            "id": str(entry.id),
            "ready_to_confirm": item.ready,
            "date": entry.occurred_on.isoformat() if entry.occurred_on else None,
            "direction": entry.direction,
            "amount": kes(entry.amount_cents),
            "with": entry.counterparty,
            "category_name": category_name(entry.category),
        }
    return shown


def _why(item: ReviewItem) -> str:
    if item.entry is None:
        return "Nothing could be read from it yet; it needs entering by hand."
    if item.match is not None:
        return "A receipt may belong to this payment."
    if item.ask_how_paid:
        return "A receipt with no payment: was it paid in cash or by card?"
    if item.ask_own_account:
        return "The payment may have gone to one of the person's own accounts."
    if item.ready:
        return "Ready to confirm as it is."
    return "Some details need checking before it can be confirmed."
