import uuid
from datetime import UTC, datetime

from jalada.modules.ledger.domain.audit import Actor, AuditAction, AuditEvent, SubjectType
from jalada.modules.ledger.domain.putting_back import status_before_rejection

NOW = datetime(2026, 11, 15, 9, tzinfo=UTC)


def rejected(before: dict[str, str] | None) -> AuditEvent:
    return AuditEvent(
        uuid.uuid4(),
        uuid.uuid4(),
        SubjectType.TRANSACTION,
        uuid.uuid4(),
        Actor.USER,
        AuditAction.REJECTED,
        before,
        {"status": "rejected"},
        NOW,
    )


def test_the_status_before_the_latest_rejection_comes_back() -> None:
    events = [rejected({"status": "proposed"}), rejected({"status": "candidate"})]

    assert status_before_rejection(events) == "candidate"


def test_anything_unknown_comes_back_as_waiting_for_a_look() -> None:
    assert status_before_rejection([]) == "needs_review"
    assert status_before_rejection([rejected(None)]) == "needs_review"
    assert status_before_rejection([rejected({"status": "confirmed"})]) == "needs_review"
