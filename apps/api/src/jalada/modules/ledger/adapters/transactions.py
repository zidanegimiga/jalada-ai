from dataclasses import asdict
from datetime import date
from uuid import UUID

from sqlalchemy import Select, and_, delete, exists, extract, func, or_, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session as DbSession

from jalada.modules.ledger.adapters import transaction_rows
from jalada.modules.ledger.adapters.tables import (
    CertificatePaymentRow,
    TransactionEvidenceRow,
    TransactionLineRow,
    TransactionRow,
)
from jalada.modules.ledger.domain.categories import Direction, Purpose
from jalada.modules.ledger.domain.ledger import LedgerFilter, LedgerPosition, Total
from jalada.modules.ledger.domain.transactions import (
    Transaction,
    TransactionKind,
    TransactionStatus,
)

PARTS = ("lines", "evidence")


class SqlTransactions:
    """One user's transactions. Every query filters by user."""

    def __init__(self, db: DbSession, user_id: UUID) -> None:
        self._db = db
        self._user_id = user_id

    def add(self, transaction: Transaction) -> None:
        self._check_owner(transaction)
        self._db.add(TransactionRow(**_fields(transaction)))
        self._db.flush()
        self._save_lines(transaction)
        self._add_links(transaction)

    def get(self, transaction_id: UUID) -> Transaction | None:
        found = self._load(self._mine().where(TransactionRow.id == transaction_id))
        return found[0] if found else None

    def pending(self, limit: int) -> list[Transaction]:
        waiting = [TransactionStatus.PROPOSED, TransactionStatus.NEEDS_REVIEW]
        query = self._mine().where(TransactionRow.status.in_(waiting))
        return self._load(query.order_by(TransactionRow.created_at).limit(limit))

    def confirmed(
        self, filters: LedgerFilter, after: LedgerPosition | None, limit: int
    ) -> list[Transaction]:
        query = self._mine().where(TransactionRow.status == TransactionStatus.CONFIRMED)
        query = query.where(*transaction_rows.conditions(filters))
        if after:
            # Keyset paging: everything strictly older than where the last page ended.
            query = query.where(
                or_(
                    TransactionRow.occurred_on < after.occurred_on,
                    and_(
                        TransactionRow.occurred_on == after.occurred_on,
                        TransactionRow.id < after.entry_id,
                    ),
                )
            )
        order = (TransactionRow.occurred_on.desc(), TransactionRow.id.desc())
        return self._load(query.order_by(*order).limit(limit))

    def all(self) -> list[Transaction]:
        return self._load(self._mine().order_by(TransactionRow.created_at, TransactionRow.id))

    def incoming(self, start: date, end: date) -> list[Transaction]:
        query = self._mine().where(
            TransactionRow.status == TransactionStatus.CONFIRMED,
            TransactionRow.kind == TransactionKind.PAYMENT,
            TransactionRow.direction == Direction.IN,
            TransactionRow.occurred_on.between(start, end),
        )
        return self._load(query.order_by(TransactionRow.occurred_on, TransactionRow.id))

    def monthly_totals(self, year: int) -> list[Total]:
        month = extract("month", TransactionRow.occurred_on)
        line = TransactionLineRow
        query = (
            select(month, TransactionRow.direction, line.purpose, func.sum(line.amount_cents))
            .join(line, line.transaction_id == TransactionRow.id)
            .where(
                TransactionRow.user_id == self._user_id,
                TransactionRow.status == TransactionStatus.CONFIRMED,
                extract("year", TransactionRow.occurred_on) == year,
                # A payment linked to a certificate is already counted in its gross amount.
                ~exists().where(CertificatePaymentRow.payment_id == TransactionRow.id),
            )
            .group_by(month, TransactionRow.direction, line.purpose)
        )
        return [
            Total(int(m), Direction(str(direction)), Purpose(purpose), int(cents or 0))
            for m, direction, purpose, cents in self._db.execute(query)
        ]

    def update(self, transaction: Transaction) -> None:
        self._check_owner(transaction)
        values = {k: v for k, v in _fields(transaction).items() if k not in ("id", "user_id")}
        updated = self._db.execute(
            update(TransactionRow)
            .where(TransactionRow.user_id == self._user_id, TransactionRow.id == transaction.id)
            .values(**values)
        )
        # Lines and links below are keyed by transaction id alone, so stop unless the row
        # above was this user's.
        if updated.rowcount != 1:  # type: ignore[attr-defined]
            raise LookupError("No such transaction for this user")
        self._db.execute(
            delete(TransactionLineRow).where(
                TransactionLineRow.user_id == self._user_id,
                TransactionLineRow.transaction_id == transaction.id,
            )
        )
        self._save_lines(transaction)
        self._add_links(transaction)

    def _save_lines(self, transaction: Transaction) -> None:
        for position, line in enumerate(transaction.lines):
            self._db.add(
                TransactionLineRow(
                    transaction_id=transaction.id,
                    position=position,
                    user_id=self._user_id,
                    **asdict(line),
                )
            )
        self._db.flush()

    def _add_links(self, transaction: Transaction) -> None:
        for link in transaction.evidence:
            self._db.execute(
                insert(TransactionEvidenceRow)
                .values(transaction_id=transaction.id, user_id=self._user_id, **asdict(link))
                .on_conflict_do_nothing()
            )

    def _mine(self) -> Select[TransactionRow]:
        return select(TransactionRow).where(TransactionRow.user_id == self._user_id)

    def _load(self, query: Select[TransactionRow]) -> list[Transaction]:
        return transaction_rows.load(self._db, list(self._db.scalars(query)))

    def _check_owner(self, transaction: Transaction) -> None:
        if transaction.user_id != self._user_id:
            raise PermissionError("Transaction belongs to another user")


def _fields(transaction: Transaction) -> dict[str, object]:
    return {k: v for k, v in asdict(transaction).items() if k not in PARTS}
