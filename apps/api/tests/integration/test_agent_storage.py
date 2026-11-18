import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session as DbSession
from sqlalchemy.orm import sessionmaker

from jalada.modules.accounts.domain.users import User
from jalada.modules.agent.application.ports import AgentRun
from jalada.modules.agent.domain.conversation import Message, Role, Thread
from jalada.modules.agent.domain.proposals import ActionKind, ActionStatus, ProposedAction
from jalada.modules.agent.domain.routing import Route
from jalada.modules.agent.domain.run import AgentStep, Outcome, StepKind
from jalada.modules.pipeline.domain.model import ModelUsage
from jalada.sql_unit_of_work import SqlUnitOfWork

pytestmark = pytest.mark.integration

NOW = datetime(2026, 11, 18, 9, 0, tzinfo=UTC)


def add_user(session_factory: sessionmaker[DbSession]) -> uuid.UUID:
    user = User(uuid.uuid4(), f"{uuid.uuid4().hex}@example.com", "J", NOW)
    with SqlUnitOfWork(session_factory) as work:
        work.users.add(user, None)
        work.commit()
    return user.id


def add_thread(session_factory: sessionmaker[DbSession], user_id: uuid.UUID) -> Thread:
    thread = Thread(uuid.uuid4(), user_id, "KPLC this quarter", NOW, NOW)
    with SqlUnitOfWork(session_factory) as work:
        work.agent_threads_for(user_id).add(thread)
        work.commit()
    return thread


def test_messages_come_back_oldest_first_within_the_window(
    session_factory: sessionmaker[DbSession],
) -> None:
    user = add_user(session_factory)
    thread = add_thread(session_factory, user)
    with SqlUnitOfWork(session_factory) as work:
        threads = work.agent_threads_for(user)
        for i in range(5):
            role = Role.PERSON if i % 2 == 0 else Role.ASSISTANT
            threads.add_message(thread.id, Message(role, f"message {i}", NOW + timedelta(i)))
        threads.touch(thread.id, NOW + timedelta(days=5))
        work.commit()

    with SqlUnitOfWork(session_factory) as work:
        threads = work.agent_threads_for(user)
        recent = threads.recent_messages(thread.id, 3)
        found = threads.get(thread.id)

    assert [m.text for m in recent] == ["message 2", "message 3", "message 4"]
    assert recent[0].role == Role.PERSON
    assert found is not None and found.updated_at == NOW + timedelta(days=5)


def test_another_persons_thread_cannot_be_read_or_written(
    session_factory: sessionmaker[DbSession],
) -> None:
    owner, other = add_user(session_factory), add_user(session_factory)
    thread = add_thread(session_factory, owner)
    with SqlUnitOfWork(session_factory) as work:
        work.agent_threads_for(owner).add_message(thread.id, Message(Role.PERSON, "mine", NOW))
        work.commit()

    with SqlUnitOfWork(session_factory) as work:
        theirs = work.agent_threads_for(other)
        assert theirs.get(thread.id) is None
        assert theirs.recent(10) == []
        assert work.agent_threads_for(owner).recent(10) == [thread]
        assert theirs.recent_messages(thread.id, 10) == []
        with pytest.raises(ValueError, match="No such thread"):
            theirs.add_message(thread.id, Message(Role.PERSON, "not mine", NOW))


def test_a_run_keeps_its_steps_in_order_and_adds_up_its_cost(
    session_factory: sessionmaker[DbSession],
) -> None:
    user = add_user(session_factory)
    thread = add_thread(session_factory, user)
    steps = (
        AgentStep(
            StepKind.MODEL,
            "gemini-3.5-flash-lite",
            "tool",
            420,
            ModelUsage(300, 40, Decimal("0.0001")),
        ),
        AgentStep(StepKind.TOOL, "search_entries", "ok", 12),
        AgentStep(
            StepKind.MODEL,
            "gemini-3.5-flash-lite",
            "answer",
            380,
            ModelUsage(500, 60, Decimal("0.0002")),
        ),
    )
    run = AgentRun(
        uuid.uuid4(),
        user,
        thread.id,
        Outcome.ANSWERED,
        steps,
        NOW,
        NOW + timedelta(seconds=1),
        Route.DEEP,
    )
    with SqlUnitOfWork(session_factory) as work:
        work.agent_runs.add(run)
        work.commit()

    with SqlUnitOfWork(session_factory) as work:
        assert work.agent_runs.for_user(user) == [run]


def test_a_suggested_change_is_kept_and_decided_only_by_its_owner(
    session_factory: sessionmaker[DbSession],
) -> None:
    owner, other = add_user(session_factory), add_user(session_factory)
    thread = add_thread(session_factory, owner)
    run_id = uuid.uuid4()
    action = ProposedAction(
        uuid.uuid4(),
        owner,
        thread.id,
        run_id,
        ActionKind.CHANGE_CATEGORY,
        {"entry_id": str(uuid.uuid4()), "category": "business_rent"},
        "Change the category to Workspace rent",
        ActionStatus.PROPOSED,
        NOW,
    )
    with SqlUnitOfWork(session_factory) as work:
        work.agent_actions_for(owner).add(action)
        work.agent_threads_for(owner).add_message(
            thread.id, Message(Role.ASSISTANT, "I can change that.", NOW, run_id)
        )
        work.commit()

    with SqlUnitOfWork(session_factory) as work:
        theirs = work.agent_actions_for(other)
        assert theirs.get(action.id) is None
        theirs.save(action.decided(ActionStatus.CONFIRMED, NOW))
        work.commit()

    with SqlUnitOfWork(session_factory) as work:
        mine = work.agent_actions_for(owner)
        assert mine.for_run(run_id) == [action], "another person cannot decide it"
        mine.save(action.decided(ActionStatus.DECLINED, NOW))
        work.commit()

    with SqlUnitOfWork(session_factory) as work:
        [found] = work.agent_actions_for(owner).for_thread(thread.id)
        [message] = work.agent_threads_for(owner).recent_messages(thread.id, 5)
    assert (found.status, found.decided_at) == (ActionStatus.DECLINED, NOW)
    assert message.run_id == run_id
