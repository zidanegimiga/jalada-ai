from fastapi import APIRouter

from jalada.dependencies import CurrentUser, ServicesDependency
from jalada.modules.ledger.api.schemas.changes import (
    EntryChangesResponse,
    decode_change_position,
)
from jalada.modules.ledger.domain.changes import START
from jalada.shared.errors import InvalidEntry

router = APIRouter(tags=["sync"])


@router.get("/v1/sync/entries")
def read_entry_changes(
    user: CurrentUser, services: ServicesDependency, after: str | None = None
) -> EntryChangesResponse:
    """Every entry saved since `after`, in any state, so a device can keep its copy up to
    date. Leave `after` out the first time to get everything."""
    position = decode_change_position(after) if after else START
    if position is None:
        raise InvalidEntry("That position in the change feed is not valid. Start again.")
    return EntryChangesResponse.from_page(services.entry_changes.since(user.id, position))
