from dataclasses import dataclass
from uuid import UUID

from jalada.modules.ledger.domain.entries import Entry


@dataclass(frozen=True, order=True)
class ChangePosition:
    """Where a device has read up to in the change feed: the database transaction that
    saved a row, then its id, to keep rows from the same transaction in order."""

    saved_in: int
    id: UUID


START = ChangePosition(0, UUID(int=0))


@dataclass(frozen=True)
class EntryChange:
    """An entry as it is now. `entry` is None when it has no entry shape, such as a receipt
    still waiting as a candidate: a device should not show it."""

    position: ChangePosition
    id: UUID
    version: int
    entry: Entry | None


@dataclass(frozen=True)
class ChangePage:
    changes: list[EntryChange]
    # Where to read from next time. Always set: a device keeps it even when nothing changed.
    next_position: ChangePosition
    # More changes are ready now: read again straight away.
    more: bool
