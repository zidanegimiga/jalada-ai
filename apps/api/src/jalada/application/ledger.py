from collections.abc import Callable
from dataclasses import dataclass
from uuid import UUID

from jalada.application.ports import UnitOfWork
from jalada.domain.entries import Entry
from jalada.domain.ledger import LedgerFilter, LedgerPosition, MonthSummary, summarise


@dataclass(frozen=True)
class LedgerPage:
    entries: list[Entry]
    # Where the next page starts, or None on the last page.
    next_position: LedgerPosition | None


class Ledger:
    """Reading confirmed entries: the list with filters, and the monthly picture."""

    def __init__(self, unit_of_work: Callable[[], UnitOfWork]) -> None:
        self._unit_of_work = unit_of_work

    def page(
        self,
        user_id: UUID,
        filters: LedgerFilter,
        after: LedgerPosition | None = None,
        size: int = 50,
    ) -> LedgerPage:
        with self._unit_of_work() as work:
            # One extra row says whether another page follows.
            entries = work.entries_for(user_id).confirmed(filters, after, size + 1)
        if len(entries) <= size:
            return LedgerPage(entries, None)
        last = entries[size - 1]
        if last.occurred_on is None:
            raise RuntimeError("A confirmed entry has no date")
        return LedgerPage(entries[:size], LedgerPosition(last.occurred_on, last.id))

    def year(self, user_id: UUID, year: int) -> list[MonthSummary]:
        with self._unit_of_work() as work:
            return summarise(work.entries_for(user_id).monthly_totals(year))
