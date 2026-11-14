"""Add transactions, their lines and the evidence about them.

Revision ID: 0010
Revises: 0009
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "transactions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=True),
        sa.Column("kind", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("occurred_on", sa.Date(), nullable=True),
        sa.Column("direction", sa.String(length=3), nullable=True),
        sa.Column("amount_cents", sa.BigInteger(), nullable=True),
        sa.Column("counterparty", sa.String(length=200), nullable=True),
        sa.Column("reference", sa.String(length=200), nullable=True),
        sa.Column("payment_code", sa.String(length=40), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["money_accounts.id"],
            name=op.f("fk_transactions_account_id_money_accounts"),
        ),
        sa.ForeignKeyConstraint(
            ["run_id"], ["pipeline_runs.id"], name=op.f("fk_transactions_run_id_pipeline_runs")
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_transactions_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_transactions")),
    )
    op.create_index(
        "ix_transactions_user_id_occurred_on",
        "transactions",
        ["user_id", "occurred_on"],
        unique=False,
    )
    op.create_index(
        "uq_transactions_user_id_payment_code",
        "transactions",
        ["user_id", "payment_code"],
        unique=True,
        postgresql_where="payment_code IS NOT NULL",
    )
    op.create_table(
        "transaction_lines",
        sa.Column("transaction_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("amount_cents", sa.BigInteger(), nullable=True),
        sa.Column("category", sa.String(length=40), nullable=True),
        sa.Column("purpose", sa.String(length=10), nullable=False),
        sa.ForeignKeyConstraint(
            ["transaction_id"],
            ["transactions.id"],
            name=op.f("fk_transaction_lines_transaction_id_transactions"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_transaction_lines_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("transaction_id", "position", name=op.f("pk_transaction_lines")),
    )
    op.create_index(
        op.f("ix_transaction_lines_user_id"), "transaction_lines", ["user_id"], unique=False
    )
    op.create_table(
        "transaction_evidence",
        sa.Column("transaction_id", sa.Uuid(), nullable=False),
        sa.Column("evidence_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("linked_by", sa.String(length=10), nullable=False),
        sa.Column("linked_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["evidence_id"],
            ["evidence.id"],
            name=op.f("fk_transaction_evidence_evidence_id_evidence"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["transaction_id"],
            ["transactions.id"],
            name=op.f("fk_transaction_evidence_transaction_id_transactions"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_transaction_evidence_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "transaction_id", "evidence_id", name=op.f("pk_transaction_evidence")
        ),
    )
    op.create_index(
        op.f("ix_transaction_evidence_evidence_id"),
        "transaction_evidence",
        ["evidence_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_transaction_evidence_user_id"), "transaction_evidence", ["user_id"], unique=False
    )


def downgrade() -> None:
    op.drop_table("transaction_evidence")
    op.drop_table("transaction_lines")
    op.drop_index("uq_transactions_user_id_payment_code", table_name="transactions")
    op.drop_index("ix_transactions_user_id_occurred_on", table_name="transactions")
    op.drop_table("transactions")
