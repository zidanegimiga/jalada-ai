"""Link withholding certificates to the payments that settled them.

Revision ID: 0008
Revises: 0007
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "certificate_payments",
        sa.Column("payment_id", sa.Uuid(), nullable=False),
        sa.Column("certificate_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("linked_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["certificate_id"],
            ["entries.id"],
            name=op.f("fk_certificate_payments_certificate_id_entries"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["payment_id"],
            ["entries.id"],
            name=op.f("fk_certificate_payments_payment_id_entries"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_certificate_payments_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("payment_id", name=op.f("pk_certificate_payments")),
    )
    op.create_index(
        op.f("ix_certificate_payments_certificate_id"),
        "certificate_payments",
        ["certificate_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_certificate_payments_user_id"), "certificate_payments", ["user_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_certificate_payments_user_id"), table_name="certificate_payments")
    op.drop_index(op.f("ix_certificate_payments_certificate_id"), table_name="certificate_payments")
    op.drop_table("certificate_payments")
