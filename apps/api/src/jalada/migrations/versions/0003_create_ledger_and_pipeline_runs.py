"""Create ledger entries, preferences and pipeline runs.

Revision ID: 0003
Revises: 0002
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "counterparty_preferences",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("counterparty_key", sa.String(length=200), nullable=False),
        sa.Column("category", sa.String(length=40), nullable=False),
        sa.Column("purpose", sa.String(length=10), nullable=False),
        sa.Column("times_used", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_counterparty_preferences_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_counterparty_preferences")),
    )
    op.create_index(
        "uq_counterparty_preferences_user_id_key",
        "counterparty_preferences",
        ["user_id", "counterparty_key"],
        unique=True,
    )
    op.create_table(
        "pipeline_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("evidence_id", sa.Uuid(), nullable=False),
        sa.Column("outcome", sa.String(length=20), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("cost_usd", sa.Numeric(precision=10, scale=6), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["evidence_id"],
            ["evidence.id"],
            name=op.f("fk_pipeline_runs_evidence_id_evidence"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_pipeline_runs_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_pipeline_runs")),
    )
    op.create_index(
        op.f("ix_pipeline_runs_evidence_id"), "pipeline_runs", ["evidence_id"], unique=False
    )
    op.create_table(
        "entries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("evidence_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("occurred_on", sa.Date(), nullable=True),
        sa.Column("direction", sa.String(length=3), nullable=True),
        sa.Column("amount_cents", sa.BigInteger(), nullable=True),
        sa.Column("counterparty", sa.String(length=200), nullable=True),
        sa.Column("reference", sa.String(length=200), nullable=True),
        sa.Column("mpesa_code", sa.String(length=10), nullable=True),
        sa.Column("certificate_serial", sa.String(length=40), nullable=True),
        sa.Column("tax_withheld_cents", sa.BigInteger(), nullable=True),
        sa.Column("purpose", sa.String(length=10), nullable=False),
        sa.Column("category", sa.String(length=40), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["evidence_id"],
            ["evidence.id"],
            name=op.f("fk_entries_evidence_id_evidence"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["run_id"], ["pipeline_runs.id"], name=op.f("fk_entries_run_id_pipeline_runs")
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_entries_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_entries")),
    )
    op.create_index(
        "ix_entries_user_id_occurred_on", "entries", ["user_id", "occurred_on"], unique=False
    )
    op.create_index(
        "uq_entries_user_id_certificate_serial",
        "entries",
        ["user_id", "certificate_serial"],
        unique=True,
        postgresql_where="certificate_serial IS NOT NULL",
    )
    op.create_index(
        "uq_entries_user_id_mpesa_code",
        "entries",
        ["user_id", "mpesa_code"],
        unique=True,
        postgresql_where="mpesa_code IS NOT NULL",
    )
    op.create_table(
        "pipeline_steps",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("step", sa.String(length=20), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("input", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("output", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("verdict", sa.String(length=20), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["pipeline_runs.id"],
            name=op.f("fk_pipeline_steps_run_id_pipeline_runs"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_pipeline_steps")),
    )
    op.create_index(op.f("ix_pipeline_steps_run_id"), "pipeline_steps", ["run_id"], unique=False)

    # Jobs queued before this revision only carried the evidence id. Add the owner's id.
    op.execute(
        """
        UPDATE jobs SET payload = payload || jsonb_build_object('user_id', evidence.user_id::text)
        FROM evidence
        WHERE jobs.payload->>'evidence_id' = evidence.id::text AND NOT jobs.payload ? 'user_id'
        """
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_pipeline_steps_run_id"), table_name="pipeline_steps")
    op.drop_table("pipeline_steps")
    op.drop_index(
        "uq_entries_user_id_mpesa_code",
        table_name="entries",
        postgresql_where="mpesa_code IS NOT NULL",
    )
    op.drop_index(
        "uq_entries_user_id_certificate_serial",
        table_name="entries",
        postgresql_where="certificate_serial IS NOT NULL",
    )
    op.drop_index("ix_entries_user_id_occurred_on", table_name="entries")
    op.drop_table("entries")
    op.drop_index(op.f("ix_pipeline_runs_evidence_id"), table_name="pipeline_runs")
    op.drop_table("pipeline_runs")
    op.drop_index("uq_counterparty_preferences_user_id_key", table_name="counterparty_preferences")
    op.drop_table("counterparty_preferences")
