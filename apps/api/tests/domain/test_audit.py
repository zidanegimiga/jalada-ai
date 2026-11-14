import json
import uuid
from datetime import UTC, date, datetime

import pytest
from samples import confirmed_entry

from jalada.modules.ledger.domain.audit import (
    Actor,
    AuditAction,
    SubjectType,
    event,
    snapshot,
)
from jalada.modules.ledger.domain.transactions import EvidenceRole, from_entry

NOW = datetime(2026, 11, 14, 9, 0, tzinfo=UTC)
USER = uuid.uuid4()


def test_a_snapshot_is_plain_values_with_lines_and_evidence() -> None:
    entry = confirmed_entry(USER, date(2026, 11, 4), 15000, "out", "personal_food")
    transaction = from_entry(entry, None, EvidenceRole.RECEIPT)

    kept = snapshot(transaction)

    assert json.loads(json.dumps(kept)) == kept, "it survives a trip through JSON"
    assert kept["id"] == str(entry.id)
    assert kept["occurred_on"] == "2026-11-04"
    assert kept["status"] == "confirmed"
    assert kept["lines"] == [
        {"amount_cents": 15000, "category": "personal_food", "purpose": "personal"}
    ]
    assert kept["evidence"][0]["role"] == "receipt"


def test_an_event_keeps_both_sides_and_who_did_it() -> None:
    entry = confirmed_entry(USER, date(2026, 11, 4), 15000, "out", "personal_food")
    before = from_entry(entry, None, EvidenceRole.OTHER)

    created = event(
        USER,
        SubjectType.TRANSACTION,
        entry.id,
        Actor.PIPELINE,
        AuditAction.PROPOSED,
        None,
        before,
        NOW,
    )

    assert created.before is None and created.after == snapshot(before)
    assert (created.actor, created.action, created.at) == (
        Actor.PIPELINE,
        AuditAction.PROPOSED,
        NOW,
    )


def test_only_records_are_kept() -> None:
    with pytest.raises(TypeError):
        snapshot({"amount": 1})
