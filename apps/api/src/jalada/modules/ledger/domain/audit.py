"""The audit trail: one event for everything that happens to the records, kept for good."""

import uuid
from dataclasses import asdict, dataclass, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum, StrEnum
from typing import Any
from uuid import UUID


class Actor(StrEnum):
    USER = "user"
    PIPELINE = "pipeline"
    SYSTEM = "system"


class AuditAction(StrEnum):
    PROPOSED = "proposed"
    CONFIRMED = "confirmed"
    CORRECTED = "corrected"
    ENTERED = "entered"
    REJECTED = "rejected"


class SubjectType(StrEnum):
    TRANSACTION = "transaction"
    # Withholding certificates, until they move off entries.
    ENTRY = "entry"


@dataclass(frozen=True)
class AuditEvent:
    id: UUID
    user_id: UUID
    subject_type: SubjectType
    subject_id: UUID
    actor: Actor
    action: AuditAction
    # The subject before and after, as plain values. None before it existed.
    before: dict[str, Any] | None
    after: dict[str, Any] | None
    at: datetime


def snapshot(subject: Any) -> dict[str, Any]:
    """A record as plain values that any program can read back: text for ids and dates."""
    if not is_dataclass(subject) or isinstance(subject, type):
        raise TypeError("Only records can be kept in the audit trail")
    return {key: _plain(item) for key, item in asdict(subject).items()}


def event(
    user_id: UUID,
    subject_type: SubjectType,
    subject_id: UUID,
    actor: Actor,
    action: AuditAction,
    before: Any,
    after: Any,
    at: datetime,
) -> AuditEvent:
    return AuditEvent(
        uuid.uuid4(),
        user_id,
        subject_type,
        subject_id,
        actor,
        action,
        snapshot(before) if before is not None else None,
        snapshot(after) if after is not None else None,
        at,
    )


def _plain(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_plain(item) for item in value]
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, UUID | date | datetime | Decimal):
        return str(value)
    return value
