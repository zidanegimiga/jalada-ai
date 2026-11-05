from datetime import date
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, Field

from jalada.api.schemas.evidence import EvidenceResponse
from jalada.application.entry_review import ReviewItem
from jalada.domain.categories import CATEGORIES, Direction
from jalada.domain.entries import Correction, Entry
from jalada.domain.money import to_cents


def _shillings_to_cents(value: object) -> object:
    """Amounts arrive as text such as "1,250.00": never floats, and never a bare number,
    which could be read as shillings or cents."""
    if value is None:
        return None
    cents = to_cents(value) if isinstance(value, str) else None
    if cents is None:
        raise ValueError("Write the amount like 1,250.00")
    return cents


Cents = Annotated[int, BeforeValidator(_shillings_to_cents), Field(gt=0)]


class CorrectionRequest(BaseModel):
    occurred_on: date | None = None
    amount: Cents | None = None
    direction: Direction | None = None
    counterparty: str | None = Field(default=None, max_length=200)
    category: str | None = None

    def to_correction(self) -> Correction:
        return Correction(
            self.occurred_on, self.amount, self.direction, self.counterparty, self.category
        )


class EntryResponse(BaseModel):
    id: UUID
    evidence_id: UUID
    kind: str
    status: str
    occurred_on: date | None
    direction: str | None
    amount_cents: int | None
    counterparty: str | None
    reference: str | None
    mpesa_code: str | None
    certificate_serial: str | None
    tax_withheld_cents: int | None
    payer_tax_number: str | None
    purpose: str
    category: str | None
    category_name: str | None
    confidence: float

    @classmethod
    def from_entry(cls, entry: Entry) -> "EntryResponse":
        category = CATEGORIES.get(entry.category or "")
        return cls(
            id=entry.id,
            evidence_id=entry.evidence_id,
            kind=entry.kind,
            status=entry.status,
            occurred_on=entry.occurred_on,
            direction=entry.direction,
            amount_cents=entry.amount_cents,
            counterparty=entry.counterparty,
            reference=entry.reference,
            mpesa_code=entry.mpesa_code,
            certificate_serial=entry.certificate_serial,
            tax_withheld_cents=entry.tax_withheld_cents,
            payer_tax_number=entry.payer_tax_number,
            purpose=entry.purpose,
            category=entry.category,
            category_name=category.name if category else None,
            confidence=entry.confidence,
        )


class ReviewItemResponse(BaseModel):
    evidence: EvidenceResponse
    # None when nothing could read the evidence and the user needs to type the entry in.
    entry: EntryResponse | None

    @classmethod
    def from_item(cls, item: ReviewItem) -> "ReviewItemResponse":
        entry = EntryResponse.from_entry(item.entry) if item.entry else None
        return cls(evidence=EvidenceResponse.from_evidence(item.evidence), entry=entry)


class ReviewQueue(BaseModel):
    items: list[ReviewItemResponse]
