"""Turning transaction rows back into transactions, a page at a time."""

from collections import defaultdict
from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
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


def load(db: DbSession, rows: Sequence[TransactionRow]) -> list[Transaction]:
    """The transactions for these rows, in the same order. Two queries for the whole page:
    one for the lines and one for the evidence links."""
    ids = [row.id for row in rows]
    lines: dict[UUID, list[TransactionLine]] = defaultdict(list)
    for line in db.scalars(
        select(TransactionLineRow)
        .where(TransactionLineRow.transaction_id.in_(ids))
        .order_by(TransactionLineRow.transaction_id, TransactionLineRow.position)
    ):
        lines[line.transaction_id].append(
            TransactionLine(line.amount_cents, line.category, Purpose(line.purpose))
        )
    links: dict[UUID, list[EvidenceLink]] = defaultdict(list)
    for link in db.scalars(
        select(TransactionEvidenceRow)
        .where(TransactionEvidenceRow.transaction_id.in_(ids))
        .order_by(TransactionEvidenceRow.linked_at, TransactionEvidenceRow.evidence_id)
    ):
        links[link.transaction_id].append(
            EvidenceLink(
                link.evidence_id, EvidenceRole(link.role), LinkedBy(link.linked_by), link.linked_at
            )
        )
    return [_transaction(row, lines[row.id], links[row.id]) for row in rows]


def _transaction(
    row: TransactionRow, lines: list[TransactionLine], links: list[EvidenceLink]
) -> Transaction:
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
        lines=tuple(lines),
        evidence=tuple(links),
    )
