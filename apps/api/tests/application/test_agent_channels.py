import uuid
from collections.abc import Sequence
from datetime import date, timedelta

import pytest
from fakes import FakeUnitOfWork, FixedClock, Store
from fakes.agent import CannedRunner
from samples import confirmed_entry

from jalada.modules.agent.application.channels import (
    ANSWER_QUESTION_JOB,
    NOTES,
    AnswerQuestionJob,
    ChannelAssistant,
)
from jalada.modules.agent.application.conversations import Conversations
from jalada.modules.agent.application.ports import TurnRequest
from jalada.modules.agent.application.proposals import ActionProposals
from jalada.modules.agent.application.tools import ToolContext
from jalada.modules.agent.domain.progress import OnProgress, ignore
from jalada.modules.agent.domain.proposals import ActionKind, ProposedAction
from jalada.modules.agent.domain.run import TurnResult
from jalada.modules.agent.wiring import build_confirmations
from jalada.modules.ledger.application.entry_review import EntryReview

ME = uuid.uuid4()
CHAT = "4242"


class Chat:
    """Records what the assistant would send in the chat app."""

    def __init__(self) -> None:
        self.answers: list[tuple[str, str, list[str]]] = []
        self.notes: list[tuple[str, str]] = []

    def answer(self, chat: str, text: str, actions: Sequence[ProposedAction]) -> None:
        self.answers.append((chat, text, [a.summary for a in actions]))

    def note(self, chat: str, text: str) -> None:
        self.notes.append((chat, text))


class Suggesting(CannedRunner):
    """Suggests moving the person's payment to Workspace rent, as a model would."""

    def __init__(self, store: Store, proposals: ActionProposals) -> None:
        super().__init__("I suggested Workspace rent. Tap Confirm to change it.")
        self.store = store
        self.proposals = proposals

    def run(self, request: TurnRequest, on_progress: OnProgress = ignore) -> TurnResult:
        [payment] = self.store.transactions.values()
        context = ToolContext(request.user_id, request.today, request.run_id, request.thread_id)
        payload = {"entry_id": str(payment.id), "category": "business_rent"}
        self.proposals.propose(context, ActionKind.CHANGE_CATEGORY, payload, "Move it to rent")
        return super().run(request, on_progress)


def assistant(
    store: Store, clock: FixedClock, chat: Chat, runner: CannedRunner
) -> ChannelAssistant:
    def work() -> FakeUnitOfWork:
        return FakeUnitOfWork(store)

    return ChannelAssistant(
        work,
        Conversations(work, runner, clock),
        build_confirmations(work, clock, EntryReview(work, clock)),
        chat,
        clock,
    )


@pytest.fixture
def payment(store: Store) -> uuid.UUID:
    entry = confirmed_entry(ME, date(2026, 7, 4), 250_000, "out", "business_other")
    store.save_entries(entry)
    return entry.id


def test_a_question_is_queued_for_the_worker(store: Store, clock: FixedClock) -> None:
    assistant(store, clock, Chat(), CannedRunner()).queue(ME, CHAT, "KPLC?")

    assert store.jobs == [
        (ANSWER_QUESTION_JOB, {"user_id": str(ME), "chat": CHAT, "question": "KPLC?"})
    ]


def test_the_worker_answers_in_the_chat(store: Store, clock: FixedClock) -> None:
    chat = Chat()

    AnswerQuestionJob(assistant(store, clock, chat, CannedRunner())).handle(
        {"user_id": str(ME), "chat": CHAT, "question": "KPLC?"}
    )

    assert chat.answers == [(CHAT, "You paid Ksh 4,500.", [])]


def test_questions_close_together_continue_one_conversation(
    store: Store, clock: FixedClock
) -> None:
    asking = assistant(store, clock, Chat(), CannedRunner())
    asking.answer(ME, CHAT, "KPLC?")
    clock.current += timedelta(minutes=10)
    asking.answer(ME, CHAT, "And rent?")
    clock.current += timedelta(hours=2)
    asking.answer(ME, CHAT, "New topic?")

    assert len(store.agent_threads) == 2


def test_a_suggestion_arrives_with_its_buttons_and_a_tap_makes_it(
    store: Store, clock: FixedClock, payment: uuid.UUID
) -> None:
    chat = Chat()

    def work() -> FakeUnitOfWork:
        return FakeUnitOfWork(store)

    asking = assistant(store, clock, chat, Suggesting(store, ActionProposals(work, clock)))
    asking.answer(ME, CHAT, "That was rent")

    [(_, _, summaries)] = chat.answers
    assert summaries == ["Move it to rent"]
    assert store.transactions[payment].lines[0].category == "business_other"

    [action] = store.agent_actions.values()
    asking.decide(ME, CHAT, action.id, confirm=True)

    assert store.transactions[payment].lines[0].category == "business_rent"
    assert chat.notes == [(CHAT, "Done: Move it to rent")]
    asking.decide(ME, CHAT, action.id, confirm=False)
    assert chat.notes[-1] == (CHAT, NOTES["gone"])


def test_another_persons_tap_changes_nothing(
    store: Store, clock: FixedClock, payment: uuid.UUID
) -> None:
    chat = Chat()

    def work() -> FakeUnitOfWork:
        return FakeUnitOfWork(store)

    asking = assistant(store, clock, chat, Suggesting(store, ActionProposals(work, clock)))
    asking.answer(ME, CHAT, "That was rent")
    [action] = store.agent_actions.values()

    asking.decide(uuid.uuid4(), "999", action.id, confirm=True)

    assert chat.notes == [("999", NOTES["missing"])]
    assert store.transactions[payment].lines[0].category == "business_other"


def test_a_failed_turn_is_told_in_the_chat_and_not_retried(store: Store, clock: FixedClock) -> None:
    class Broken(CannedRunner):
        def run(self, request: TurnRequest, on_progress: OnProgress = ignore) -> TurnResult:
            raise RuntimeError("model down")

    chat = Chat()

    AnswerQuestionJob(assistant(store, clock, chat, Broken())).handle(
        {"user_id": str(ME), "chat": CHAT, "question": "KPLC?"}
    )

    assert chat.notes == [(CHAT, NOTES["failed"])]
