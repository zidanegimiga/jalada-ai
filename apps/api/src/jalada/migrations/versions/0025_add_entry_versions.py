"""Give entries and transactions a version, and the database transaction that last changed
them, so edits from an older copy are caught and devices can follow changes.

Revision ID: 0025
Revises: 0024
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0025"
down_revision: str | None = "0024"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLES = ("entries", "transactions")
CURRENT_TRANSACTION = sa.text("(pg_current_xact_id()::text::bigint)")


def upgrade() -> None:
    for table in TABLES:
        op.add_column(
            table,
            sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        )
        # Existing rows all get this migration's transaction, which is fine: they are older
        # than anything a device has seen.
        op.add_column(
            table,
            sa.Column(
                "changed_in", sa.BigInteger(), server_default=CURRENT_TRANSACTION, nullable=False
            ),
        )
        op.create_index(
            op.f(f"ix_{table}_user_id_changed_in"), table, ["user_id", "changed_in", "id"]
        )


def downgrade() -> None:
    for table in TABLES:
        op.drop_index(op.f(f"ix_{table}_user_id_changed_in"), table_name=table)
        op.drop_column(table, "changed_in")
        op.drop_column(table, "version")
