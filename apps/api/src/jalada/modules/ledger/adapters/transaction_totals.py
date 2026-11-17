"""Totals of confirmed payment lines, for the monthly view and the category breakdown.

Transfers between the user's own accounts are neither in nor out, and a payment linked to a
certificate is already counted in the certificate's gross amount, so both are left out."""

from datetime import date
from uuid import UUID

from sqlalchemy import ColumnElement, exists, extract, func, select
from sqlalchemy.orm import Session as DbSession

from jalada.modules.ledger.adapters.tables import (
    CertificatePaymentRow,
    TransactionLineRow,
    TransactionRow,
)
from jalada.modules.ledger.domain.categories import Direction, Purpose
from jalada.modules.ledger.domain.ledger import CategoryTotal, Total
from jalada.modules.ledger.domain.transactions import TransactionKind, TransactionStatus


def _counted(user_id: UUID) -> list[ColumnElement[bool]]:
    return [
        TransactionRow.user_id == user_id,
        TransactionRow.status == TransactionStatus.CONFIRMED,
        TransactionRow.kind != TransactionKind.TRANSFER,
        ~exists().where(CertificatePaymentRow.payment_id == TransactionRow.id),
    ]


def monthly(db: DbSession, user_id: UUID, year: int) -> list[Total]:
    """Confirmed lines per month, direction and purpose in one year."""
    month = extract("month", TransactionRow.occurred_on)
    line = TransactionLineRow
    query = (
        select(month, TransactionRow.direction, line.purpose, func.sum(line.amount_cents))
        .join(line, line.transaction_id == TransactionRow.id)
        .where(*_counted(user_id), extract("year", TransactionRow.occurred_on) == year)
        .group_by(month, TransactionRow.direction, line.purpose)
    )
    return [
        Total(int(m), Direction(str(direction)), Purpose(purpose), int(cents or 0))
        for m, direction, purpose, cents in db.execute(query)
    ]


def by_category(db: DbSession, user_id: UUID, start: date, end: date) -> list[CategoryTotal]:
    """Confirmed lines per direction and category between two dates, both included."""
    line = TransactionLineRow
    query = (
        select(TransactionRow.direction, line.category, func.sum(line.amount_cents))
        .join(line, line.transaction_id == TransactionRow.id)
        .where(*_counted(user_id), TransactionRow.occurred_on.between(start, end))
        .group_by(TransactionRow.direction, line.category)
    )
    return [
        CategoryTotal(Direction(str(direction)), category, int(cents or 0))
        for direction, category, cents in db.execute(query)
    ]
