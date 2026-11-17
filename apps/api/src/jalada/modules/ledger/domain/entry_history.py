"""A payment's history in plain terms, read from its audit events."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from jalada.modules.ledger.domain.audit import Actor, AuditAction, AuditEvent

# The fields a person would notice changing, by the name the screens use for them.
TRACKED = {
    "amount_cents": "amount",
    "occurred_on": "date",
    "counterparty": "who",
    "direction": "direction",
    "lines": "category",
    "to_account_id": "account",
}


@dataclass(frozen=True)
class HistoryItem:
    at: datetime
    actor: Actor
    action: AuditAction
    # What changed, in TRACKED's words, when the event changed the payment.
    changed: tuple[str, ...]


def _changed(before: dict[str, Any] | None, after: dict[str, Any] | None) -> tuple[str, ...]:
    if before is None or after is None:
        return ()
    return tuple(name for key, name in TRACKED.items() if before.get(key) != after.get(key))


def history(events: list[AuditEvent]) -> list[HistoryItem]:
    """Oldest first, as the events were written."""
    return [HistoryItem(e.at, e.actor, e.action, _changed(e.before, e.after)) for e in events]
