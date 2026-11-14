"""Payments now live only as transactions, so remove their old entries. Entries are kept for
withholding certificates.

Every payment entry has had a transaction with the same id since migration 0011, kept in
step until payments moved over, and its history is in the audit trail since migration 0012.
The removal stops if any payment entry has no transaction. Going back puts the entries back
from the transactions.

Revision ID: 0014
Revises: 0013
"""

from collections.abc import Sequence

from alembic import op
from sqlalchemy import text

revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

WITHOUT_TRANSACTION = """
SELECT count(*) FROM entries e
WHERE e.kind = 'transaction'
  AND NOT EXISTS (SELECT 1 FROM transactions t WHERE t.id = e.id AND t.user_id = e.user_id)
"""

PUT_BACK = """
INSERT INTO entries (
    id, user_id, evidence_id, run_id, kind, status, occurred_on, direction, amount_cents,
    counterparty, reference, mpesa_code, certificate_serial, tax_withheld_cents, purpose,
    category, confidence, created_at, confirmed_at, payer_tax_number
)
SELECT
    t.id, t.user_id,
    (SELECT x.evidence_id FROM transaction_evidence x
     WHERE x.transaction_id = t.id ORDER BY x.linked_at, x.evidence_id LIMIT 1),
    t.run_id, 'transaction', t.status, t.occurred_on, t.direction, t.amount_cents,
    t.counterparty, t.reference, t.payment_code, NULL, NULL, l.purpose, l.category,
    t.confidence, t.created_at, t.confirmed_at, NULL
FROM transactions t
JOIN transaction_lines l ON l.transaction_id = t.id AND l.position = 0
WHERE t.status <> 'candidate'
  AND EXISTS (SELECT 1 FROM transaction_evidence x WHERE x.transaction_id = t.id)
  AND NOT EXISTS (SELECT 1 FROM entries e WHERE e.id = t.id)
"""


def upgrade() -> None:
    connection = op.get_bind()
    missing = connection.execute(text(WITHOUT_TRANSACTION)).scalar_one()
    if missing:
        # Raising rolls the migration back, so nothing is removed.
        raise RuntimeError(f"{missing} payment entries have no transaction")
    connection.execute(text("DELETE FROM entries WHERE kind = 'transaction'"))


def downgrade() -> None:
    op.get_bind().execute(text(PUT_BACK))
