"""Changes the assistant suggests. Nothing changes until the person confirms with a tap."""

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import StrEnum
from uuid import UUID

# A suggestion is only good while the records it was based on are likely unchanged.
LIFETIME = timedelta(hours=24)


class ActionKind(StrEnum):
    CONFIRM_PAYMENT = "confirm_payment"
    CHANGE_CATEGORY = "change_category"


class ActionStatus(StrEnum):
    PROPOSED = "proposed"
    CONFIRMED = "confirmed"
    DECLINED = "declined"
    EXPIRED = "expired"


@dataclass(frozen=True)
class ProposedAction:
    id: UUID
    user_id: UUID
    thread_id: UUID
    run_id: UUID
    kind: ActionKind
    # What the change needs, such as the payment id and the new category.
    payload: dict[str, str]
    # Written by the app from the records, never by the model: this is what the person agrees to.
    summary: str
    status: ActionStatus
    created_at: datetime
    decided_at: datetime | None = None

    @property
    def expires_at(self) -> datetime:
        return self.created_at + LIFETIME

    def status_at(self, now: datetime) -> ActionStatus:
        if self.status == ActionStatus.PROPOSED and now >= self.expires_at:
            return ActionStatus.EXPIRED
        return self.status

    def decided(self, status: ActionStatus, at: datetime) -> "ProposedAction":
        return replace(self, status=status, decided_at=at)
