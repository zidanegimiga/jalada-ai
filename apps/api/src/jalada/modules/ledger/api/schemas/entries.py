from datetime import date
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, Field

from jalada.modules.evidence.api.schemas.evidence import EvidenceResponse
from jalada.modules.ledger.application.review_queue import ReviewItem, SuggestedMatch
from jalada.modules.ledger.domain.categories import CATEGORIES, Direction, Purpose
from jalada.modules.ledger.domain.entries import Correction, Entry, EntryKind, EntryStatus
from jalada.modules.ledger.domain.how_paid import PaidWith
from jalada.shared.money import to_cents


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
    payer_tax_number: str | None
    purpose: Purpose
    category: str | None
    category_name: str | None
    confidence: float
    # True when the category is only a suggestion: the user should check it, not just confirm.
    category_suggested: bool = False
    # Set on a payment linked to a withholding certificate.
    linked_certificate_id: UUID | None = None
    # Set on a certificate: the payments linked to it.
    linked_payment_ids: list[UUID] = Field(default_factory=list)

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


class SuggestedMatchResponse(BaseModel):
    """A receipt that may belong to the payment in the same item."""

    suggestion_id: UUID
    receipt: EvidenceResponse
    occurred_on: date | None
    amount_cents: int | None
    counterparty: str | None
    # What the two have in common, such as "same amount" and "same day".
    reasons: list[str]

    @classmethod
    def from_match(cls, match: SuggestedMatch) -> "SuggestedMatchResponse":
        candidate = match.candidate
        return cls(
            suggestion_id=match.suggestion.id,
            receipt=EvidenceResponse.from_evidence(match.receipt),
            occurred_on=candidate.occurred_on,
            amount_cents=candidate.amount_cents,
            counterparty=candidate.counterparty,
            reasons=list(match.suggestion.reasons),
        )


class ReviewItemResponse(BaseModel):
    evidence: EvidenceResponse
    # None when nothing could read the evidence and the user needs to type the entry in.
    entry: EntryResponse | None
    # Set when the question is whether a receipt belongs to this payment.
    match: SuggestedMatchResponse | None = None
    # True when the entry is a receipt whose payment never arrived: was it cash or card?
    ask_how_paid: bool = False
    # A receipt the user said belongs to this payment, which they can still take back.
    linked_receipt: SuggestedMatchResponse | None = None
    # True when the payment can be confirmed as it is, so it can go in Confirm all.
    ready: bool = False
    # True when the payment went to a paybill that may be the user's own account.
    ask_own_account: bool = False

    @classmethod
    def from_item(cls, item: ReviewItem) -> "ReviewItemResponse":
        entry = None
        if item.entry:
            entry = EntryResponse.from_entry(item.entry)
            entry.category_suggested = item.category_suggested
        match = SuggestedMatchResponse.from_match(item.match) if item.match else None
        return cls(
            evidence=EvidenceResponse.from_evidence(item.evidence),
            entry=entry,
            match=match,
            ask_how_paid=item.ask_how_paid,
            linked_receipt=(
                SuggestedMatchResponse.from_match(item.linked_receipt)
                if item.linked_receipt
                else None
            ),
            ready=item.ready,
            ask_own_account=item.ask_own_account,
        )


class ConfirmAllRequest(BaseModel):
    # The ready payments the user saw listed. To check never shows more than 100 items.
    entry_ids: list[UUID] = Field(min_length=1, max_length=100)


class ConfirmAllResponse(BaseModel):
    # Only what was still ready. Anything else stays on To check.
    confirmed: list[EntryResponse]


class HowPaidRequest(BaseModel):
    paid_with: PaidWith


class ReviewQueue(BaseModel):
    items: list[ReviewItemResponse]
