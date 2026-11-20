"""Keep the answers to writes sent with an Idempotency-Key, so a retry is applied once.

Revision ID: 0024
Revises: 0023
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0024"
down_revision: str | None = "0023"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "idempotency_keys",
        sa.Column("owner_hash", sa.String(length=64), nullable=False),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("status", sa.SmallInteger(), nullable=True),
        sa.Column("content_type", sa.String(length=100), nullable=True),
        sa.Column("body", sa.LargeBinary(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["owner_hash"],
            ["sessions.token_hash"],
            name=op.f("fk_idempotency_keys_owner_hash_sessions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("owner_hash", "key", name=op.f("pk_idempotency_keys")),
    )


def downgrade() -> None:
    op.drop_table("idempotency_keys")
