"""Add the changes the assistant suggests, and which turn each answer came from.

Revision ID: 0020
Revises: 0019
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0020"
down_revision: str | None = "0019"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_actions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("thread_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=30), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("summary", sa.String(length=300), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["thread_id"],
            ["agent_threads.id"],
            name=op.f("fk_agent_actions_thread_id_agent_threads"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_agent_actions_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_agent_actions")),
    )
    op.create_index(op.f("ix_agent_actions_run_id"), "agent_actions", ["run_id"], unique=False)
    op.create_index(
        op.f("ix_agent_actions_thread_id"), "agent_actions", ["thread_id"], unique=False
    )
    op.create_index(op.f("ix_agent_actions_user_id"), "agent_actions", ["user_id"], unique=False)
    op.add_column("agent_messages", sa.Column("run_id", sa.Uuid(), nullable=True))


def downgrade() -> None:
    op.drop_column("agent_messages", "run_id")
    op.drop_index(op.f("ix_agent_actions_user_id"), table_name="agent_actions")
    op.drop_index(op.f("ix_agent_actions_thread_id"), table_name="agent_actions")
    op.drop_index(op.f("ix_agent_actions_run_id"), table_name="agent_actions")
    op.drop_table("agent_actions")
