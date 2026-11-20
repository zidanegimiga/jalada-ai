from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, LargeBinary, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from jalada.core.database.base import Base


class IdempotencyKeyRow(Base):
    """One write's answer, per session and key. Signing out removes them with the session."""

    __tablename__ = "idempotency_keys"

    owner_hash: Mapped[str] = mapped_column(
        String(64), ForeignKey("sessions.token_hash", ondelete="CASCADE"), primary_key=True
    )
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    fingerprint: Mapped[str] = mapped_column(String(64))
    # Empty while the first try runs.
    status: Mapped[int | None] = mapped_column(SmallInteger)
    content_type: Mapped[str | None] = mapped_column(String(100))
    body: Mapped[bytes | None] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
