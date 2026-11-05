"""Let entries be confirmed, corrected and typed in by hand, keeping every revision.

Revision ID: 0004
Revises: 0003
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "entry_revisions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("entry_id", sa.Uuid(), nullable=False),
        sa.Column("before", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("after", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["entry_id"],
            ["entries.id"],
            name=op.f("fk_entry_revisions_entry_id_entries"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_entry_revisions")),
    )
    op.create_index(
        op.f("ix_entry_revisions_entry_id"), "entry_revisions", ["entry_id"], unique=False
    )
    op.add_column("entries", sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True))
    op.alter_column("entries", "run_id", existing_type=sa.UUID(), nullable=True)


def downgrade() -> None:
    op.alter_column("entries", "run_id", existing_type=sa.UUID(), nullable=False)
    op.drop_column("entries", "confirmed_at")
    op.drop_index(op.f("ix_entry_revisions_entry_id"), table_name="entry_revisions")
    op.drop_table("entry_revisions")
