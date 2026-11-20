"""The change feed's conditions, the same for every table that has `changed_in`."""

from sqlalchemy import ColumnElement, tuple_

from jalada.modules.ledger.adapters.tables import EntryRow, TransactionRow
from jalada.modules.ledger.domain.changes import ChangePosition


def changed_after(
    row: type[EntryRow] | type[TransactionRow], after: ChangePosition, until: int
) -> list[ColumnElement[bool]]:
    """Saved after `after`, by a database transaction that has certainly finished."""
    return [
        tuple_(row.changed_in, row.id) > tuple_(after.saved_in, after.id),
        row.changed_in < until,
    ]
