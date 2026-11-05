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
    # None for entries typed in by hand, which no pipeline run produced.
    run_id: UUID | None
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
    confirmed_at: datetime | None = None
    # From withholding certificates: the payer's KRA PIN.
    payer_tax_number: str | None = None


def counterparty_key(name: str) -> str:
    """One form per counterparty, so 'JANE  WANJIKU' and 'jane wanjiku' match."""
    return " ".join(name.lower().split())


@dataclass(frozen=True)
class Correction:
    """What the user changed while reviewing. None means keep the value."""

    occurred_on: date | None = None
    amount_cents: int | None = None
    direction: Direction | None = None
    counterparty: str | None = None
    category: str | None = None


def missing_fields(entry: Entry) -> list[str]:
    """Fields a confirmed entry must have."""
    required = {
        "date": entry.occurred_on,
        "amount": entry.amount_cents,
        "direction": entry.direction,
        "category": entry.category,
    }
    return [name for name, value in required.items() if value is None]
