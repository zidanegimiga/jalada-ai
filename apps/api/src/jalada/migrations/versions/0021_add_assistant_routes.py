"""Record whether each assistant turn went to the fast or the deep models.

Revision ID: 0021
Revises: 0020
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0021"
down_revision: str | None = "0020"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "agent_runs",
        sa.Column("route", sa.String(length=10), server_default="fast", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("agent_runs", "route")
