import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Predictable constraint names, so migrations can refer to them.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class UserRow(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True)
    password_hash: Mapped[str | None] = mapped_column(Text)
    google_subject: Mapped[str | None] = mapped_column(String(255), unique=True)
    display_name: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SessionRow(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class EvidenceRow(Base):
    __tablename__ = "evidence"
    __table_args__ = (
        # The same file or text is only processed once per user.
        Index("uq_evidence_user_id_sha256", "user_id", "sha256", unique=True),
        Index("ix_evidence_user_id_received_at", "user_id", "received_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    source: Mapped[str] = mapped_column(String(20))
    kind: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(20))
    content_type: Mapped[str] = mapped_column(String(50))
    size_bytes: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    encryption_key_id: Mapped[str] = mapped_column(String(32))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class JobRow(Base):
    __tablename__ = "jobs"
    __table_args__ = (Index("ix_jobs_status_run_after", "status", "run_after"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    kind: Mapped[str] = mapped_column(String(50))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(20), default="queued")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    run_after: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)


class PipelineRunRow(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    evidence_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("evidence.id", ondelete="CASCADE"), index=True
    )
    outcome: Mapped[str] = mapped_column(String(20))
    attempts: Mapped[int] = mapped_column(Integer)
    input_tokens: Mapped[int] = mapped_column(Integer)
    output_tokens: Mapped[int] = mapped_column(Integer)
    cost_usd: Mapped[Any] = mapped_column(Numeric(10, 6))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class PipelineStepRow(Base):
    __tablename__ = "pipeline_steps"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("pipeline_runs.id", ondelete="CASCADE"), index=True
    )
    step: Mapped[str] = mapped_column(String(20))
    attempt: Mapped[int] = mapped_column(Integer)
    input: Mapped[dict[str, Any]] = mapped_column(JSONB)
    output: Mapped[dict[str, Any]] = mapped_column(JSONB)
    verdict: Mapped[str] = mapped_column(String(20))
    duration_ms: Mapped[int] = mapped_column(Integer)


class EntryRow(Base):
    __tablename__ = "entries"
    __table_args__ = (
        # The duplicate guards: one entry per M-Pesa code and per certificate, per user.
        Index(
            "uq_entries_user_id_mpesa_code",
            "user_id",
            "mpesa_code",
            unique=True,
            postgresql_where="mpesa_code IS NOT NULL",
        ),
        Index(
            "uq_entries_user_id_certificate_serial",
            "user_id",
            "certificate_serial",
            unique=True,
            postgresql_where="certificate_serial IS NOT NULL",
        ),
        Index("ix_entries_user_id_occurred_on", "user_id", "occurred_on"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    evidence_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("evidence.id", ondelete="CASCADE"))
    run_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("pipeline_runs.id"))
    kind: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(20))
    occurred_on: Mapped[Any] = mapped_column(Date, nullable=True)
    direction: Mapped[str | None] = mapped_column(String(3))
    amount_cents: Mapped[int | None] = mapped_column(BigInteger)
    counterparty: Mapped[str | None] = mapped_column(String(200))
    reference: Mapped[str | None] = mapped_column(String(200))
    mpesa_code: Mapped[str | None] = mapped_column(String(10))
    certificate_serial: Mapped[str | None] = mapped_column(String(40))
    tax_withheld_cents: Mapped[int | None] = mapped_column(BigInteger)
    purpose: Mapped[str] = mapped_column(String(10))
    category: Mapped[str | None] = mapped_column(String(40))
    confidence: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class EntryRevisionRow(Base):
    """Every confirmation and correction, with the entry before and after."""

    __tablename__ = "entry_revisions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    entry_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("entries.id", ondelete="CASCADE"), index=True
    )
    before: Mapped[dict[str, Any]] = mapped_column(JSONB)
    after: Mapped[dict[str, Any]] = mapped_column(JSONB)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class CounterpartyPreferenceRow(Base):
    __tablename__ = "counterparty_preferences"
    __table_args__ = (
        Index(
            "uq_counterparty_preferences_user_id_key", "user_id", "counterparty_key", unique=True
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    counterparty_key: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(40))
    purpose: Mapped[str] = mapped_column(String(10))
    times_used: Mapped[int] = mapped_column(Integer)
