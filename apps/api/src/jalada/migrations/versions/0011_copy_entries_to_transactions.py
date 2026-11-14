"""Copy every transaction entry that has no transaction yet, then check they all match.

Entries written since transactions were added already have one. Each copy keeps its
entry's id, gets one line with the entry's category and purpose, and links its evidence in
the role its kind gives it. M-Pesa messages go on the user's M-Pesa account.

Revision ID: 0011
Revises: 0010
"""

from collections.abc import Sequence

from alembic import op
from sqlalchemy import text

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

COPY_TRANSACTIONS = """
INSERT INTO transactions (
    id, user_id, account_id, kind, status, occurred_on, direction, amount_cents,
    counterparty, reference, payment_code, confidence, run_id, created_at, confirmed_at
)
SELECT
    e.id, e.user_id,
    CASE WHEN ev.kind = 'mpesa_message' THEN (
        SELECT m.id FROM money_accounts m
        WHERE m.user_id = e.user_id AND m.kind = 'mpesa'
        ORDER BY m.created_at LIMIT 1
    ) END,
    'payment', e.status, e.occurred_on, e.direction, e.amount_cents,
    e.counterparty, e.reference, e.mpesa_code, e.confidence, e.run_id, e.created_at,
    e.confirmed_at
FROM entries e
JOIN evidence ev ON ev.id = e.evidence_id
WHERE e.kind = 'transaction'
  AND NOT EXISTS (SELECT 1 FROM transactions t WHERE t.id = e.id)
"""

COPY_LINES = """
INSERT INTO transaction_lines (transaction_id, position, user_id, amount_cents, category, purpose)
SELECT e.id, 0, e.user_id, e.amount_cents, e.category, e.purpose
FROM entries e
WHERE e.kind = 'transaction'
  AND NOT EXISTS (SELECT 1 FROM transaction_lines l WHERE l.transaction_id = e.id)
"""

COPY_LINKS = """
INSERT INTO transaction_evidence (transaction_id, evidence_id, user_id, role, linked_by, linked_at)
SELECT
    e.id, e.evidence_id, e.user_id,
    CASE ev.kind
        WHEN 'mpesa_message' THEN 'payment_proof'
        WHEN 'receipt' THEN 'receipt'
        WHEN 'statement' THEN 'statement'
        WHEN 'payslip' THEN 'payslip'
        WHEN 'withholding_certificate' THEN 'certificate'
        ELSE 'other'
    END,
    CASE WHEN e.run_id IS NULL THEN 'user' ELSE 'pipeline' END,
    e.created_at
FROM entries e
JOIN evidence ev ON ev.id = e.evidence_id
WHERE e.kind = 'transaction'
  AND NOT EXISTS (
      SELECT 1 FROM transaction_evidence x
      WHERE x.transaction_id = e.id AND x.evidence_id = e.evidence_id
  )
"""

# Entries whose transaction is missing or says something different.
MISMATCHES = """
SELECT count(*)
FROM entries e
LEFT JOIN transactions t ON t.id = e.id AND t.user_id = e.user_id
LEFT JOIN transaction_lines l ON l.transaction_id = e.id AND l.position = 0
WHERE e.kind = 'transaction'
  AND (
      t.id IS NULL
      OR t.status <> e.status
      OR t.occurred_on IS DISTINCT FROM e.occurred_on
      OR t.direction IS DISTINCT FROM e.direction
      OR t.amount_cents IS DISTINCT FROM e.amount_cents
      OR t.payment_code IS DISTINCT FROM e.mpesa_code
      OR l.amount_cents IS DISTINCT FROM e.amount_cents
      OR l.category IS DISTINCT FROM e.category
      OR l.purpose IS DISTINCT FROM e.purpose
      OR (SELECT count(*) FROM transaction_lines o WHERE o.transaction_id = e.id) <> 1
  )
"""


def upgrade() -> None:
    connection = op.get_bind()
    for statement in (COPY_TRANSACTIONS, COPY_LINES, COPY_LINKS):
        connection.execute(text(statement))
    mismatches = connection.execute(text(MISMATCHES)).scalar_one()
    if mismatches:
        # Raising rolls the whole migration back, so nothing half copied is left behind.
        raise RuntimeError(f"{mismatches} entries do not match their transactions")


def downgrade() -> None:
    # Copies cannot be told apart from transactions written beside new entries, and both
    # stay correct, so there is nothing to undo.
    pass
