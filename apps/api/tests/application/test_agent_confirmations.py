import uuid
from collections.abc import Mapping
from datetime import date, timedelta

import pytest
from fakes import FakeUnitOfWork, FixedClock, Store
from samples import confirmed_entry

from jalada.modules.agent.application.confirmations import ActionConfirmations
from jalada.modules.agent.domain.proposals import ActionKind, ActionStatus, ProposedAction
from jalada.modules.agent.wiring import build_confirmations
from jalada.modules.ledger.application.entry_review import EntryReview
from jalada.shared.errors import ActionClosed, ActionNotFound, InvalidEntry

ME, SOMEONE_ELSE = uuid.uuid4(), uuid.uuid4()


def suggest(store: Store, clock: FixedClock, payload: dict[str, str]) -> ProposedAction:
    action = ProposedAction(
        uuid.uuid4(),
        ME,
        uuid.uuid4(),
        uuid.uuid4(),
        ActionKind.CHANGE_CATEGORY,
        payload,
        "Move it to Workspace rent",
        ActionStatus.PROPOSED,
        clock.now(),
    )
    store.agent_actions[action.id] = action
    return action


def confirmations(store: Store, clock: FixedClock) -> ActionConfirmations:
    def work() -> FakeUnitOfWork:
        return FakeUnitOfWork(store)

    return build_confirmations(work, clock, EntryReview(work, clock))


def a_payment(store: Store) -> uuid.UUID:
    entry = confirmed_entry(ME, date(2026, 7, 4), 250_000, "out", "business_other")
    store.save_entries(entry)
    return entry.id


def test_confirming_makes_the_change_through_the_ledger(store: Store, clock: FixedClock) -> None:
    payment = a_payment(store)
    action = suggest(store, clock, {"entry_id": str(payment), "category": "business_rent"})

    done = confirmations(store, clock).confirm(ME, action.id)

    assert (done.status, done.decided_at) == (ActionStatus.CONFIRMED, clock.now())
    assert store.transactions[payment].lines[0].category == "business_rent"
    assert store.agent_actions[action.id].status == ActionStatus.CONFIRMED
    assert store.audit_events[-1].action == "corrected", "kept in the payment's history"


def test_declining_changes_nothing(store: Store, clock: FixedClock) -> None:
    payment = a_payment(store)
    action = suggest(store, clock, {"entry_id": str(payment), "category": "business_rent"})

    declined = confirmations(store, clock).decline(ME, action.id)

    assert declined.status == ActionStatus.DECLINED
    assert store.transactions[payment].lines[0].category == "business_other"


def test_a_change_is_made_once(store: Store, clock: FixedClock) -> None:
    payment = a_payment(store)
    action = suggest(store, clock, {"entry_id": str(payment), "category": "business_rent"})
    deciding = confirmations(store, clock)
    deciding.confirm(ME, action.id)

    with pytest.raises(ActionClosed):
        deciding.confirm(ME, action.id)
    with pytest.raises(ActionClosed):
        deciding.decline(ME, action.id)


def test_a_suggestion_cannot_be_confirmed_after_a_day(store: Store, clock: FixedClock) -> None:
    payment = a_payment(store)
    action = suggest(store, clock, {"entry_id": str(payment), "category": "business_rent"})
    clock.current += timedelta(hours=25)

    with pytest.raises(ActionClosed):
        confirmations(store, clock).confirm(ME, action.id)
    assert store.transactions[payment].lines[0].category == "business_other"


def test_another_person_cannot_decide(store: Store, clock: FixedClock) -> None:
    payment = a_payment(store)
    action = suggest(store, clock, {"entry_id": str(payment), "category": "business_rent"})

    with pytest.raises(ActionNotFound):
        confirmations(store, clock).confirm(SOMEONE_ELSE, action.id)
    assert store.agent_actions[action.id].status == ActionStatus.PROPOSED


def test_a_change_the_ledger_refuses_stays_undecided(store: Store, clock: FixedClock) -> None:
    def refuse(user_id: uuid.UUID, payload: Mapping[str, str]) -> None:
        raise InvalidEntry("The payment changed since.")

    action = suggest(store, clock, {"entry_id": str(uuid.uuid4()), "category": "x"})
    deciding = ActionConfirmations(
        lambda: FakeUnitOfWork(store), clock, {ActionKind.CHANGE_CATEGORY: refuse}
    )

    with pytest.raises(InvalidEntry):
        deciding.confirm(ME, action.id)
    assert store.agent_actions[action.id].status == ActionStatus.PROPOSED
