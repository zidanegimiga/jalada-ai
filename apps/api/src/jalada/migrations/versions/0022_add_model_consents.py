"""Add each person's agreement to have a model read their records.

Revision ID: 0022
Revises: 0021
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0022"
down_revision: str | None = "0021"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "model_consents",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("notice", sa.String(length=500), nullable=False),
        sa.Column("given_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_model_consents_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id", name=op.f("pk_model_consents")),
    )


def downgrade() -> None:
    op.drop_table("model_consents")
