from collections.abc import Callable
from uuid import UUID

from jalada.modules.ledger.domain.changes import (
    ChangePage,
    ChangePosition,
    EntryChange,
)
from jalada.modules.ledger.domain.transactions import Transaction, TransactionStatus, as_entry
from jalada.unit_of_work import UnitOfWork

PAGE_SIZE = 200


def _as_change(position: ChangePosition, transaction: Transaction) -> EntryChange:
    shown = transaction.status != TransactionStatus.CANDIDATE and transaction.evidence
    entry = as_entry(transaction) if shown else None
    return EntryChange(position, transaction.id, transaction.version, entry)


class EntryChanges:
    """What changed in a person's entries since a device last asked, oldest first, so the
    desktop app can keep its copy without reading everything again (decision 0029)."""

    def __init__(self, unit_of_work: Callable[[], UnitOfWork]) -> None:
        self._unit_of_work = unit_of_work

    def since(self, user_id: UUID, after: ChangePosition, limit: int = PAGE_SIZE) -> ChangePage:
        with self._unit_of_work() as work:
            # Asked first, so every save it lets through has finished before the reads.
            until = work.settled_before()
            payments = work.transactions_for(user_id).changed_after(after, until, limit + 1)
            certificates = work.entries_for(user_id).changed_after(after, until, limit + 1)
        found = sorted(
            [_as_change(position, t) for position, t in payments]
            + [EntryChange(position, e.id, e.version, e) for position, e in certificates],
            key=lambda change: change.position,
        )
        page = found[:limit]
        if len(found) > limit:
            return ChangePage(page, page[-1].position, more=True)
        # Everything before `until` has been read; later saves come next time.
        return ChangePage(page, max(after, ChangePosition(until, UUID(int=0))), more=False)
