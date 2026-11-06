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
    String,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from jalada.core.database.base import Base


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
    payer_tax_number: Mapped[str | None] = mapped_column(String(20))


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


class CertificatePaymentRow(Base):
    """A payment that settled a withholding certificate. Each payment settles one at most."""

    __tablename__ = "certificate_payments"

    payment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("entries.id", ondelete="CASCADE"), primary_key=True
    )
    certificate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("entries.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    linked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


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
