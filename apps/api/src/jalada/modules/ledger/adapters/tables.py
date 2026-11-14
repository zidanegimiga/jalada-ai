import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Identity,
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
        ForeignKey("transactions.id", ondelete="CASCADE"), primary_key=True
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


class MoneyAccountRow(Base):
    """Somewhere the user's money sits: M-Pesa, a bank, cash, a card or a loan."""

    __tablename__ = "money_accounts"
    __table_args__ = (Index("uq_money_accounts_user_id_name", "user_id", "name", unique=True),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(10))
    name: Mapped[str] = mapped_column(String(80))
    tracked: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class TransactionRow(Base):
    """Money that moved, in or out of one of the user's accounts."""

    __tablename__ = "transactions"
    __table_args__ = (
        # One transaction per payment system code, per user: the duplicate guard.
        Index(
            "uq_transactions_user_id_payment_code",
            "user_id",
            "payment_code",
            unique=True,
            postgresql_where="payment_code IS NOT NULL",
        ),
        Index("ix_transactions_user_id_occurred_on", "user_id", "occurred_on"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    account_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("money_accounts.id"))
    kind: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(20))
    occurred_on: Mapped[Any] = mapped_column(Date, nullable=True)
    direction: Mapped[str | None] = mapped_column(String(3))
    amount_cents: Mapped[int | None] = mapped_column(BigInteger)
    counterparty: Mapped[str | None] = mapped_column(String(200))
    reference: Mapped[str | None] = mapped_column(String(200))
    payment_code: Mapped[str | None] = mapped_column(String(40))
    confidence: Mapped[float] = mapped_column(Float)
    run_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("pipeline_runs.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class TransactionLineRow(Base):
    """What part of a transaction was for, in order."""

    __tablename__ = "transaction_lines"

    transaction_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("transactions.id", ondelete="CASCADE"), primary_key=True
    )
    position: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    amount_cents: Mapped[int | None] = mapped_column(BigInteger)
    category: Mapped[str | None] = mapped_column(String(40))
    purpose: Mapped[str] = mapped_column(String(10))


class TransactionEvidenceRow(Base):
    """Evidence about a transaction, and what it does for it."""

    __tablename__ = "transaction_evidence"

    transaction_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("transactions.id", ondelete="CASCADE"), primary_key=True
    )
    evidence_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("evidence.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(20))
    linked_by: Mapped[str] = mapped_column(String(10))
    linked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AuditEventRow(Base):
    """Everything that happened to the records. Rows are only ever added."""

    __tablename__ = "audit_events"
    __table_args__ = (Index("ix_audit_events_user_id_subject_id", "user_id", "subject_id"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    # The order events were written in, for events with the same time.
    seq: Mapped[int] = mapped_column(BigInteger, Identity(always=True))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    subject_type: Mapped[str] = mapped_column(String(20))
    subject_id: Mapped[uuid.UUID]
    actor: Mapped[str] = mapped_column(String(10))
    action: Mapped[str] = mapped_column(String(20))
    before: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    after: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
