from dataclasses import dataclass, field
from datetime import date
from uuid import UUID

from jalada.modules.ledger.domain.categories import Direction, Purpose


@dataclass(frozen=True)
class LedgerFilter:
    start: date | None = None
    end: date | None = None
    direction: Direction | None = None
    purpose: Purpose | None = None
    category: str | None = None


@dataclass(frozen=True)
class LedgerPosition:
    """Where a page of the ledger ended: newest first, so by date and then id."""

    occurred_on: date
    entry_id: UUID


@dataclass(frozen=True)
class Total:
    month: int
    direction: Direction
    purpose: Purpose
    cents: int


@dataclass(frozen=True)
class CategoryTotal:
    """Confirmed money in one direction and category. `category` is None for money that
    was confirmed without one."""

    direction: Direction
    category: str | None
    cents: int


def combine(totals: list[CategoryTotal]) -> list[CategoryTotal]:
    """Adds up totals from several sources by direction and category, largest first."""
    sums: dict[tuple[Direction, str | None], int] = {}
    for total in totals:
        key = (total.direction, total.category)
        sums[key] = sums.get(key, 0) + total.cents
    combined = [CategoryTotal(d, c, cents) for (d, c), cents in sums.items() if cents]
    return sorted(combined, key=lambda t: t.cents, reverse=True)


@dataclass
class MonthSummary:
    """Money in and out for one month, in cents, split between business and personal."""

    month: int
    money_in: dict[Purpose, int] = field(default_factory=dict)
    money_out: dict[Purpose, int] = field(default_factory=dict)


def summarise(totals: list[Total]) -> list[MonthSummary]:
    months = [MonthSummary(month) for month in range(1, 13)]
    for total in totals:
        side = (
            months[total.month - 1].money_in
            if total.direction == Direction.IN
            else (months[total.month - 1].money_out)
        )
        side[total.purpose] = side.get(total.purpose, 0) + total.cents
    return months
