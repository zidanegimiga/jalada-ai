"""Add transfers: how messages name an account, and where a transfer went.

Revision ID: 0018
Revises: 0017
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0018"
down_revision: str | None = "0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "money_accounts",
        sa.Column(
            "identifiers",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
    )
    op.add_column("transactions", sa.Column("to_account_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        op.f("fk_transactions_to_account_id_money_accounts"),
        "transactions",
        "money_accounts",
        ["to_account_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_transactions_to_account_id_money_accounts"), "transactions", type_="foreignkey"
    )
    op.drop_column("transactions", "to_account_id")
    op.drop_column("money_accounts", "identifiers")
