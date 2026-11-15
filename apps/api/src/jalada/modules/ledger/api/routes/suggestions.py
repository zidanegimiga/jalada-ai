from uuid import UUID

from fastapi import APIRouter, status

from jalada.dependencies import CurrentUser, ServicesDependency
from jalada.modules.ledger.api.schemas.entries import EntryResponse

router = APIRouter(tags=["review"])


@router.post("/v1/suggestions/{suggestion_id}/accept")
def accept_suggestion(
    suggestion_id: UUID, user: CurrentUser, services: ServicesDependency
) -> EntryResponse:
    """Yes, the receipt and the payment are the same purchase. Returns the payment, which
    still needs confirming."""
    return EntryResponse.from_entry(services.matches.accept(user.id, suggestion_id))


@router.post("/v1/suggestions/{suggestion_id}/decline", status_code=status.HTTP_204_NO_CONTENT)
def decline_suggestion(
    suggestion_id: UUID, user: CurrentUser, services: ServicesDependency
) -> None:
    """No, they are not the same. The pair is never offered again."""
    services.matches.decline(user.id, suggestion_id)


@router.post("/v1/suggestions/{suggestion_id}/undo")
def undo_suggestion(
    suggestion_id: UUID, user: CurrentUser, services: ServicesDependency
) -> EntryResponse:
    """Takes back a yes: the receipt waits for its payment again, and the pair is not
    offered again. Returns the payment."""
    return EntryResponse.from_entry(services.matches.undo(user.id, suggestion_id))
