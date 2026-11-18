import uuid
from datetime import UTC, datetime, timedelta

from jalada.modules.agent.domain.proposals import ActionKind, ActionStatus, ProposedAction

NOW = datetime(2026, 11, 18, 9, 0, tzinfo=UTC)


def proposed() -> ProposedAction:
    return ProposedAction(
        uuid.uuid4(),
        uuid.uuid4(),
        uuid.uuid4(),
        uuid.uuid4(),
        ActionKind.CONFIRM_PAYMENT,
        {"entry_id": "x"},
        "Confirm Ksh 150.00 to JANE",
        ActionStatus.PROPOSED,
        NOW,
    )


def test_a_suggestion_lasts_a_day() -> None:
    action = proposed()

    assert action.status_at(NOW + timedelta(hours=23)) == ActionStatus.PROPOSED
    assert action.status_at(NOW + timedelta(hours=24)) == ActionStatus.EXPIRED


def test_a_decision_is_kept_after_the_day_is_over() -> None:
    decided = proposed().decided(ActionStatus.CONFIRMED, NOW)

    assert decided.status_at(NOW + timedelta(days=3)) == ActionStatus.CONFIRMED
    assert decided.decided_at == NOW
