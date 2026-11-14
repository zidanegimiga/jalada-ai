from dataclasses import asdict
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session as DbSession

from jalada.modules.ledger.adapters.tables import (
    TransactionEvidenceRow,
    TransactionLineRow,
    TransactionRow,
)
from jalada.modules.ledger.domain.categories import Direction, Purpose
from jalada.modules.ledger.domain.transactions import (
    EvidenceLink,
    EvidenceRole,
    LinkedBy,
    Transaction,
    TransactionKind,
    TransactionLine,
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
        row = self._db.scalar(
            select(TransactionRow).where(
                TransactionRow.user_id == self._user_id, TransactionRow.id == transaction_id
            )
        )
        return self._to_transaction(row) if row else None

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

    def _to_transaction(self, row: TransactionRow) -> Transaction:
        lines = self._db.scalars(
            select(TransactionLineRow)
            .where(TransactionLineRow.transaction_id == row.id)
            .order_by(TransactionLineRow.position)
        )
        links = self._db.scalars(
            select(TransactionEvidenceRow)
            .where(TransactionEvidenceRow.transaction_id == row.id)
            .order_by(TransactionEvidenceRow.linked_at)
        )
        return Transaction(
            id=row.id,
            user_id=row.user_id,
            account_id=row.account_id,
            kind=TransactionKind(row.kind),
            status=TransactionStatus(row.status),
            occurred_on=row.occurred_on,
            direction=Direction(row.direction) if row.direction else None,
            amount_cents=row.amount_cents,
            counterparty=row.counterparty,
            reference=row.reference,
            payment_code=row.payment_code,
            confidence=row.confidence,
            run_id=row.run_id,
            created_at=row.created_at,
            confirmed_at=row.confirmed_at,
            lines=tuple(
                TransactionLine(line.amount_cents, line.category, Purpose(line.purpose))
                for line in lines
            ),
            evidence=tuple(
                EvidenceLink(
                    link.evidence_id,
                    EvidenceRole(link.role),
                    LinkedBy(link.linked_by),
                    link.linked_at,
                )
                for link in links
            ),
        )

    def _check_owner(self, transaction: Transaction) -> None:
        if transaction.user_id != self._user_id:
            raise PermissionError("Transaction belongs to another user")


def _fields(transaction: Transaction) -> dict[str, object]:
    return {k: v for k, v in asdict(transaction).items() if k not in PARTS}
