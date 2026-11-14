"""Add money accounts, and give every existing user M-Pesa and Cash.

Revision ID: 0009
Revises: 0008
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "money_accounts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=10), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("tracked", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_money_accounts_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_money_accounts")),
    )
    op.create_index(
        "uq_money_accounts_user_id_name", "money_accounts", ["user_id", "name"], unique=True
    )
    # The same accounts sign-up opens for new users.
    op.execute(
        """
        INSERT INTO money_accounts (id, user_id, kind, name, tracked, created_at)
        SELECT gen_random_uuid(), users.id, defaults.kind, defaults.name, true, now()
        FROM users
        CROSS JOIN (VALUES ('mpesa', 'M-Pesa'), ('cash', 'Cash')) AS defaults (kind, name)
        """
    )


def downgrade() -> None:
    op.drop_index("uq_money_accounts_user_id_name", table_name="money_accounts")
    op.drop_table("money_accounts")
