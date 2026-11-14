"""Add the audit trail, and copy every entry revision into it.

A revision that ended rejected becomes a rejection; every other one a confirmation. The
copies keep the entry as it was recorded then.

Revision ID: 0012
Revises: 0011
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("seq", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("subject_type", sa.String(length=20), nullable=False),
        sa.Column("subject_id", sa.Uuid(), nullable=False),
        sa.Column("actor", sa.String(length=10), nullable=False),
        sa.Column("action", sa.String(length=20), nullable=False),
        sa.Column("before", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("after", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_audit_events_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_events")),
    )
    op.create_index(
        "ix_audit_events_user_id_subject_id",
        "audit_events",
        ["user_id", "subject_id"],
        unique=False,
    )
    op.execute(
        """
        INSERT INTO audit_events (id, user_id, subject_type, subject_id, actor, action,
                                  before, after, at)
        SELECT gen_random_uuid(), e.user_id,
               CASE WHEN e.kind = 'transaction' THEN 'transaction' ELSE 'entry' END,
               r.entry_id, 'user',
               CASE WHEN r.after ->> 'status' = 'rejected' THEN 'rejected' ELSE 'confirmed' END,
               r.before, r.after, r.changed_at
        FROM entry_revisions r
        JOIN entries e ON e.id = r.entry_id
        ORDER BY r.changed_at, r.id
        """
    )


def downgrade() -> None:
    op.drop_index("ix_audit_events_user_id_subject_id", table_name="audit_events")
    op.drop_table("audit_events")
