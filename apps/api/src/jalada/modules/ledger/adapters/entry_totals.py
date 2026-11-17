"""Totals of confirmed entries (withholding certificates while both models exist), for the
monthly view and the category breakdown. A payment linked to a certificate is already counted
in the certificate's gross amount, so it is left out."""

from datetime import date
from uuid import UUID

from sqlalchemy import ColumnElement, exists, extract, func, select
from sqlalchemy.orm import Session as DbSession

from jalada.modules.ledger.adapters.tables import CertificatePaymentRow, EntryRow
from jalada.modules.ledger.domain.categories import Direction, Purpose
from jalada.modules.ledger.domain.entries import EntryKind, EntryStatus
from jalada.modules.ledger.domain.ledger import CategoryTotal, Total


def _counted(user_id: UUID, kind: EntryKind | None) -> list[ColumnElement[bool]]:
    return [
        EntryRow.user_id == user_id,
        EntryRow.status == EntryStatus.CONFIRMED,
        ~exists().where(CertificatePaymentRow.payment_id == EntryRow.id),
        *([EntryRow.kind == kind] if kind else []),
    ]


def monthly(db: DbSession, user_id: UUID, year: int, kind: EntryKind | None) -> list[Total]:
    """Confirmed entries per month, direction and purpose in one year."""
    month = extract("month", EntryRow.occurred_on)
    query = (
        select(month, EntryRow.direction, EntryRow.purpose, func.sum(EntryRow.amount_cents))
        .where(*_counted(user_id, kind), extract("year", EntryRow.occurred_on) == year)
        .group_by(month, EntryRow.direction, EntryRow.purpose)
    )
    return [
        Total(int(m), Direction(str(direction)), Purpose(purpose), int(cents or 0))
        for m, direction, purpose, cents in db.execute(query)
    ]


def by_category(
    db: DbSession, user_id: UUID, start: date, end: date, kind: EntryKind | None
) -> list[CategoryTotal]:
    """Confirmed entries per direction and category between two dates, both included."""
    query = (
        select(EntryRow.direction, EntryRow.category, func.sum(EntryRow.amount_cents))
        .where(*_counted(user_id, kind), EntryRow.occurred_on.between(start, end))
        .group_by(EntryRow.direction, EntryRow.category)
    )
    return [
        CategoryTotal(Direction(str(direction)), category, int(cents or 0))
        for direction, category, cents in db.execute(query)
    ]
