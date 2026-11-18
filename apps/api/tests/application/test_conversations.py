import uuid

import pytest
from fakes import FakeUnitOfWork, FixedClock, Store
from fakes.agent import CannedRunner

from jalada.modules.agent.application.conversations import (
    HISTORY_MESSAGES,
    Conversations,
    EmptyQuestion,
    ThreadNotFound,
)
from jalada.modules.agent.domain.conversation import MAX_MESSAGE_LENGTH, Role
from jalada.modules.agent.domain.run import Outcome

USER = uuid.uuid4()
OTHER = uuid.uuid4()


def conversations(store: Store, runner: CannedRunner) -> Conversations:
    return Conversations(lambda: FakeUnitOfWork(store), runner, FixedClock())


def test_a_first_question_starts_a_thread_named_after_it(store: Store) -> None:
    runner = CannedRunner()

    reply = conversations(store, runner).ask(USER, "  How much did I pay KPLC? ")

    thread = store.agent_threads[reply.thread_id]
    assert (thread.user_id, thread.title) == (USER, "How much did I pay KPLC?")
    assert (reply.text, reply.outcome) == ("You paid Ksh 4,500.", Outcome.ANSWERED)
    assert [(m.role, m.text) for _, m in store.agent_messages] == [
        (Role.PERSON, "How much did I pay KPLC?"),
        (Role.ASSISTANT, "You paid Ksh 4,500."),
    ]


def test_the_runner_gets_the_user_for_tools_and_the_earlier_messages(store: Store) -> None:
    runner = CannedRunner()
    asking = conversations(store, runner)
    first = asking.ask(USER, "KPLC?")

    asking.ask(USER, "And Safaricom?", first.thread_id)

    request = runner.requests[-1]
    assert request.user_id == USER
    assert request.question == "And Safaricom?"
    assert [m.text for m in request.history] == ["KPLC?", "You paid Ksh 4,500."]


def test_only_the_last_messages_are_sent(store: Store) -> None:
    runner = CannedRunner()
    asking = conversations(store, runner)
    thread = asking.ask(USER, "question 0").thread_id
    for i in range(1, 8):
        asking.ask(USER, f"question {i}", thread)

    assert len(runner.requests[-1].history) == HISTORY_MESSAGES


def test_each_turn_is_recorded_with_its_steps(store: Store) -> None:
    runner = CannedRunner(text="I could not find that.", outcome=Outcome.WITHHELD)

    reply = conversations(store, runner).ask(USER, "KPLC?")

    [run] = store.agent_runs
    assert (run.user_id, run.thread_id, run.outcome) == (USER, reply.thread_id, Outcome.WITHHELD)
    assert run.id == runner.requests[0].run_id
    assert run.steps == runner.result.steps


def test_another_persons_thread_cannot_be_continued(store: Store) -> None:
    asking = conversations(store, CannedRunner())
    theirs = asking.ask(OTHER, "Rent?").thread_id

    with pytest.raises(ThreadNotFound):
        asking.ask(USER, "What did they ask?", theirs)
    assert len(store.agent_messages) == 2


def test_an_empty_question_is_refused_and_a_long_one_is_cut(store: Store) -> None:
    runner = CannedRunner()
    asking = conversations(store, runner)

    with pytest.raises(EmptyQuestion):
        asking.ask(USER, "   ")
    asking.ask(USER, "x" * (MAX_MESSAGE_LENGTH + 50))

    assert len(runner.requests[0].question) == MAX_MESSAGE_LENGTH
