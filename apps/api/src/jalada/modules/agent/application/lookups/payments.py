from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field

from jalada.modules.agent.application.lookups.shapes import kes, payment, unknown_category
from jalada.modules.agent.application.tools import Tool, ToolContext
from jalada.modules.ledger.application.ledger import Ledger
from jalada.modules.ledger.domain.categories import CATEGORIES, Direction
from jalada.modules.ledger.domain.ledger import LedgerFilter

# Adding up stops here, so one question cannot read a whole ledger many times over.
MAX_ADDED = 5000
PAGE = 200


class PaymentFilters(BaseModel):
    counterparty: str | None = Field(
        None, max_length=60, description="Words in who the money was with, such as KPLC."
    )
    start: date | None = Field(None, description="First day to include, YYYY-MM-DD.")
    end: date | None = Field(None, description="Last day to include, YYYY-MM-DD.")
    direction: Literal["in", "out"] | None = Field(None, description="Money in or out.")
    category: str | None = Field(None, max_length=40, description="A category slug.")

    def to_filter(self) -> LedgerFilter:
        return LedgerFilter(
            start=self.start,
            end=self.end,
            direction=Direction(self.direction) if self.direction else None,
            category=self.category,
            search=self.counterparty.strip() if self.counterparty else None,
        )


class SearchArguments(PaymentFilters):
    limit: int = Field(10, ge=1, le=20, description="How many to show, newest first.")


class SearchPayments(Tool[SearchArguments]):
    name = "search_payments"
    description = "Confirmed payments in and out, newest first, filtered as asked."
    arguments = SearchArguments

    def __init__(self, ledger: Ledger) -> None:
        self._ledger = ledger

    def run(self, context: ToolContext, arguments: SearchArguments) -> dict[str, Any]:
        if arguments.category and arguments.category not in CATEGORIES:
            return unknown_category(arguments.category)
        page = self._ledger.page(context.user_id, arguments.to_filter(), size=arguments.limit)
        return {
            "payments": [payment(entry) for entry in page.entries],
            "more_not_shown": page.next_position is not None,
        }


class AddUpPayments(Tool[PaymentFilters]):
    name = "add_up_payments"
    description = (
        "How much money went in and out, and how many payments, filtered as asked. "
        "Use it for totals instead of adding up a search."
    )
    arguments = PaymentFilters

    def __init__(self, ledger: Ledger) -> None:
        self._ledger = ledger

    def run(self, context: ToolContext, arguments: PaymentFilters) -> dict[str, Any]:
        if arguments.category and arguments.category not in CATEGORIES:
            return unknown_category(arguments.category)
        filters = arguments.to_filter()
        totals = {Direction.IN: 0, Direction.OUT: 0}
        count, after, complete = 0, None, True
        while True:
            page = self._ledger.page(context.user_id, filters, after, size=PAGE)
            for entry in page.entries:
                if entry.direction is not None and entry.amount_cents is not None:
                    totals[entry.direction] += entry.amount_cents
                    count += 1
            after = page.next_position
            if after is None:
                break
            if count >= MAX_ADDED:
                complete = False
                break
        return {
            "payments": count,
            "money_in": kes(totals[Direction.IN]),
            "money_out": kes(totals[Direction.OUT]),
            "from": _day(arguments.start),
            "to": _day(arguments.end),
            "complete": complete,
        }


def _day(day: date | None) -> str:
    return day.isoformat() if day else "any"
