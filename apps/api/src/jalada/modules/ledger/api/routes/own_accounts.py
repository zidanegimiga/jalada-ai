from uuid import UUID

from fastapi import APIRouter

from jalada.dependencies import CurrentUser, ServicesDependency
from jalada.modules.ledger.api.schemas.entries import EntryResponse

router = APIRouter(tags=["review"])


@router.post("/v1/payments/{entry_id}/own-account")
def say_the_account_is_mine(
    entry_id: UUID, user: CurrentUser, services: ServicesDependency
) -> EntryResponse:
    """The paybill account this payment went to is the user's own. Returns the payment as
    a transfer, which still needs confirming."""
    return EntryResponse.from_entry(services.own_accounts.say_mine(user.id, entry_id))
