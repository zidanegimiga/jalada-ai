from collections.abc import Callable
from dataclasses import dataclass, field
from uuid import UUID

from jalada.modules.ledger.application import records
from jalada.modules.ledger.domain.entries import Entry
from jalada.modules.ledger.domain.ledger import (
    LedgerFilter,
    LedgerPosition,
    MonthSummary,
    summarise,
)
from jalada.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class LedgerPage:
    entries: list[Entry]
    # Where the next page starts, or None on the last page.
    next_position: LedgerPosition | None
    # Payment id to certificate id, for every link the user has made.
    certificate_payments: dict[UUID, UUID] = field(default_factory=dict)


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
            entries = records.confirmed(work, user_id, filters, after, size + 1)
            links = work.certificate_payments_for(user_id).links()
        if len(entries) <= size:
            return LedgerPage(entries, None, links)
        last = entries[size - 1]
        if last.occurred_on is None:
            raise RuntimeError("A confirmed entry has no date")
        return LedgerPage(entries[:size], LedgerPosition(last.occurred_on, last.id), links)

    def year(self, user_id: UUID, year: int) -> list[MonthSummary]:
        with self._unit_of_work() as work:
            return summarise(records.monthly_totals(work, user_id, year))
