"""Point certificate links at transactions instead of entries.

Every linked payment already has a transaction with the same id (migration 0011), so the
new constraint holds for every existing row.

Revision ID: 0013
Revises: 0012
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLE = "certificate_payments"


def upgrade() -> None:
    op.drop_constraint("fk_certificate_payments_payment_id_entries", TABLE, type_="foreignkey")
    op.create_foreign_key(
        op.f("fk_certificate_payments_payment_id_transactions"),
        TABLE,
        "transactions",
        ["payment_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_certificate_payments_payment_id_transactions", TABLE, type_="foreignkey")
    op.create_foreign_key(
        op.f("fk_certificate_payments_payment_id_entries"),
        TABLE,
        "entries",
        ["payment_id"],
        ["id"],
        ondelete="CASCADE",
    )
