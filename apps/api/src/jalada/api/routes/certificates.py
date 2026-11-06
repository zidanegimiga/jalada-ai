from uuid import UUID

from fastapi import APIRouter

from jalada.api.dependencies import CurrentUser, ServicesDependency
from jalada.api.schemas.certificates import CertificateResponse, LinkPaymentRequest

router = APIRouter(tags=["certificates"])


@router.get("/v1/certificates/{certificate_id}")
def read_certificate(
    certificate_id: UUID, user: CurrentUser, services: ServicesDependency
) -> CertificateResponse:
    """A withholding certificate, the payments linked to it, and likely payments to link."""
    view = services.certificate_payments.view(user.id, certificate_id)
    return CertificateResponse.from_view(view)


@router.post("/v1/certificates/{certificate_id}/payments")
def link_payment(
    certificate_id: UUID,
    body: LinkPaymentRequest,
    user: CurrentUser,
    services: ServicesDependency,
) -> CertificateResponse:
    view = services.certificate_payments.link(user.id, certificate_id, body.payment_id)
    return CertificateResponse.from_view(view)


@router.delete("/v1/certificates/{certificate_id}/payments/{payment_id}")
def unlink_payment(
    certificate_id: UUID, payment_id: UUID, user: CurrentUser, services: ServicesDependency
) -> CertificateResponse:
    view = services.certificate_payments.unlink(user.id, certificate_id, payment_id)
    return CertificateResponse.from_view(view)
