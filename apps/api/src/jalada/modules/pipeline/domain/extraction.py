from dataclasses import asdict, dataclass
from datetime import date
from typing import Any

from jalada.modules.evidence.domain.evidence import EvidenceKind
from jalada.modules.ledger.domain.categories import Direction, Purpose


@dataclass(frozen=True)
class Extraction:
    """Fields read from one piece of evidence. Amounts are in cents."""

    kind: EvidenceKind
    occurred_on: date | None
    direction: Direction | None
    amount_cents: int | None
    counterparty: str | None = None
    reference: str | None = None
    mpesa_code: str | None = None
    fee_cents: int | None = None
    certificate_serial: str | None = None
    tax_withheld_cents: int | None = None
    tax_rate_percent: str | None = None
    payer_tax_number: str | None = None
    nature: str | None = None

    def to_record(self) -> dict[str, Any]:
        record = asdict(self)
        record["occurred_on"] = self.occurred_on.isoformat() if self.occurred_on else None
        return record


@dataclass(frozen=True)
class Classification:
    purpose: Purpose
    category: str | None
    confidence: float
    # Where the answer came from: "preference", "rule" or "none".
    source: str
