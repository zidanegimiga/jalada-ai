"""Mark the categories a model suggested, so they are shown as suggestions until the user
accepts or changes them, and send the payments they are on to "needs a look".

Revision ID: 0016
Revises: 0015
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0016"
down_revision: str | None = "0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "transaction_lines",
        sa.Column("suggested", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    # Categories a model chose on payments still waiting for the user become suggestions.
    op.execute(
        """
        UPDATE transaction_lines l SET suggested = true
        FROM transactions t, pipeline_steps s
        WHERE l.transaction_id = t.id
          AND t.status IN ('proposed', 'needs_review')
          AND l.category IS NOT NULL
          AND s.run_id = t.run_id AND s.step = 'classify' AND s.input ->> 'source' = 'model'
        """
    )
    # A suggestion is never ready to confirm as it is, so those payments need a look, and
    # so does the evidence they came from.
    op.execute(
        """
        UPDATE transactions t SET status = 'needs_review'
        WHERE t.status = 'proposed'
          AND EXISTS (
              SELECT 1 FROM transaction_lines l
              WHERE l.transaction_id = t.id AND l.suggested
          )
        """
    )
    op.execute(
        """
        UPDATE evidence e SET status = 'needs_review'
        FROM transaction_evidence x, transactions t
        WHERE x.evidence_id = e.id AND x.transaction_id = t.id
          AND e.status = 'proposed' AND t.status = 'needs_review'
        """
    )


def downgrade() -> None:
    op.drop_column("transaction_lines", "suggested")
