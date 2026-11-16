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


@router.post("/v1/payments/{entry_id}/own-account/undo")
def take_back_the_account(
    entry_id: UUID, user: CurrentUser, services: ServicesDependency
) -> EntryResponse:
    """The account is not the user's after all. Returns the payment, with what it was for
    still to choose."""
    return EntryResponse.from_entry(services.own_accounts.take_back(user.id, entry_id))
