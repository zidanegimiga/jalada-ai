from uuid import UUID

from pydantic import BaseModel

from jalada.api.schemas.entries import EntryResponse
from jalada.application.certificate_payments import CertificateView
from jalada.domain.certificates import expected_payment_cents


class LinkPaymentRequest(BaseModel):
    payment_id: UUID


class CertificateResponse(BaseModel):
    certificate: EntryResponse
    # Gross minus tax withheld: what the client would have paid in.
    expected_payment_cents: int
    linked_cents: int
    payments: list[EntryResponse]
    suggestions: list[EntryResponse]

    @classmethod
    def from_view(cls, view: CertificateView) -> "CertificateResponse":
        return cls(
            certificate=EntryResponse.from_entry(view.certificate),
            expected_payment_cents=expected_payment_cents(view.certificate),
            linked_cents=sum(p.amount_cents or 0 for p in view.payments),
            payments=[EntryResponse.from_entry(p) for p in view.payments],
            suggestions=[EntryResponse.from_entry(s) for s in view.suggestions],
        )
