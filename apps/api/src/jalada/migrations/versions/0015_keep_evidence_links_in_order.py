"""Keep evidence links in the order they were added.

The first link is the evidence a transaction came from, so the order must not depend on two
links having different times. Every link so far is a transaction's only one, so numbering
the existing rows in any order is safe.

Revision ID: 0015
Revises: 0014
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0015"
down_revision: str | None = "0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "transaction_evidence",
        sa.Column("seq", sa.BigInteger(), sa.Identity(always=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("transaction_evidence", "seq")
