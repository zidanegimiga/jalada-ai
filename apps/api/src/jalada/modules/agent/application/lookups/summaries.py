from datetime import date
from typing import Any

from pydantic import BaseModel, Field

from jalada.modules.agent.application.lookups.shapes import category_name, kes
from jalada.modules.agent.application.tools import Tool, ToolContext
from jalada.modules.ledger.application.ledger import Ledger
from jalada.modules.ledger.domain.categories import Direction


class PeriodArguments(BaseModel):
    start: date | None = Field(None, description="First day, YYYY-MM-DD. Default: 1 January.")
    end: date | None = Field(None, description="Last day, YYYY-MM-DD. Default: today.")


class SpendingByCategory(Tool[PeriodArguments]):
    name = "totals_by_category"
    description = "Money in and out between two dates, added up by category, largest first."
    arguments = PeriodArguments

    def __init__(self, ledger: Ledger) -> None:
        self._ledger = ledger

    def run(self, context: ToolContext, arguments: PeriodArguments) -> dict[str, Any]:
        end = arguments.end or context.today
        start = arguments.start or date(end.year, 1, 1)
        totals = self._ledger.categories(context.user_id, start, end)
        sides: dict[Direction, list[dict[str, Any]]] = {Direction.IN: [], Direction.OUT: []}
        for total in totals:
            sides[total.direction].append(
                {
                    "category": total.category,
                    "category_name": category_name(total.category) or "No category",
                    "amount": kes(total.cents),
                }
            )
        return {
            "from": start.isoformat(),
            "to": end.isoformat(),
            "money_in": sides[Direction.IN],
            "money_out": sides[Direction.OUT],
        }


class YearArguments(BaseModel):
    year: int | None = Field(None, ge=2000, le=2100, description="Default: this year.")


class MonthlySummary(Tool[YearArguments]):
    name = "monthly_summary"
    description = "Money in and out for each month of a year, split into business and personal."
    arguments = YearArguments

    def __init__(self, ledger: Ledger) -> None:
        self._ledger = ledger

    def run(self, context: ToolContext, arguments: YearArguments) -> dict[str, Any]:
        year = arguments.year or context.today.year
        months = []
        totals = {"money_in": 0, "money_out": 0}
        for month in self._ledger.year(context.user_id, year):
            if not (month.money_in or month.money_out):
                continue
            months.append(
                {
                    "month": f"{year}-{month.month:02d}",
                    "money_in": {purpose: kes(c) for purpose, c in month.money_in.items()},
                    "money_out": {purpose: kes(c) for purpose, c in month.money_out.items()},
                }
            )
            totals["money_in"] += sum(month.money_in.values())
            totals["money_out"] += sum(month.money_out.values())
        return {
            "year": year,
            "months": months,
            "year_money_in": kes(totals["money_in"]),
            "year_money_out": kes(totals["money_out"]),
        }
