from uuid import UUID

from fastapi import APIRouter

from jalada.dependencies import CurrentUser, ServicesDependency
from jalada.modules.ledger.api.schemas.entries import EntryResponse, HowPaidRequest

router = APIRouter(tags=["review"])


@router.post("/v1/receipts/{entry_id}/paid")
def say_how_a_receipt_was_paid(
    entry_id: UUID, body: HowPaidRequest, user: CurrentUser, services: ServicesDependency
) -> EntryResponse:
    """For a receipt whose payment never arrived. Returns the payment, which still needs
    confirming."""
    return EntryResponse.from_entry(services.how_paid.answer(user.id, entry_id, body.paid_with))
