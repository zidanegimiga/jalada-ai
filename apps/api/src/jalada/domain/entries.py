from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from jalada.domain.categories import Direction, Purpose


class EntryKind(StrEnum):
    TRANSACTION = "transaction"
    WITHHOLDING_CERTIFICATE = "withholding_certificate"


class EntryStatus(StrEnum):
    PROPOSED = "proposed"
    NEEDS_REVIEW = "needs_review"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


@dataclass(frozen=True)
class Entry:
    id: UUID
    user_id: UUID
    evidence_id: UUID
    run_id: UUID
    kind: EntryKind
    status: EntryStatus
    occurred_on: date | None
    direction: Direction | None
    amount_cents: int | None
    counterparty: str | None
    reference: str | None
    mpesa_code: str | None
    certificate_serial: str | None
    tax_withheld_cents: int | None
    purpose: Purpose
    category: str | None
    confidence: float
    created_at: datetime


def counterparty_key(name: str) -> str:
    """One form per counterparty, so 'JANE  WANJIKU' and 'jane wanjiku' match."""
    return " ".join(name.lower().split())
