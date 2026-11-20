import base64
import binascii
from uuid import UUID

from pydantic import BaseModel

from jalada.modules.ledger.api.schemas.entries import EntryResponse
from jalada.modules.ledger.domain.changes import ChangePage, ChangePosition, EntryChange


def encode_change_position(position: ChangePosition) -> str:
    raw = f"{position.saved_in}|{position.id}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def decode_change_position(cursor: str) -> ChangePosition | None:
    """None for a cursor that was not made by `encode_change_position`."""
    try:
        saved_in, change_id = base64.urlsafe_b64decode(cursor.encode()).decode().split("|")
        position = ChangePosition(int(saved_in), UUID(change_id))
    except (ValueError, binascii.Error):
        return None
    return position if position.saved_in >= 0 else None


class EntryChangeResponse(BaseModel):
    id: UUID
    version: int
    # The entry as it is now. None when it is not something to show, such as a receipt
    # still waiting as a candidate: remove any copy of it.
    entry: EntryResponse | None

    @classmethod
    def from_change(cls, change: EntryChange) -> "EntryChangeResponse":
        entry = EntryResponse.from_entry(change.entry) if change.entry else None
        return cls(id=change.id, version=change.version, entry=entry)


class EntryChangesResponse(BaseModel):
    """Entries saved since `after`, oldest first. Keep `next` and send it as `after` next
    time; when `more` is true, ask again straight away."""

    changes: list[EntryChangeResponse]
    next: str
    more: bool

    @classmethod
    def from_page(cls, page: ChangePage) -> "EntryChangesResponse":
        return cls(
            changes=[EntryChangeResponse.from_change(change) for change in page.changes],
            next=encode_change_position(page.next_position),
            more=page.more,
        )
