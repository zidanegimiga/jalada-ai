"""Nobody's records go to a model until they have agreed to the provider named now."""

import uuid

import pytest
from fakes import (
    FakeEvidenceStore,
    FakeTextReader,
    FakeUnitOfWork,
    FixedClock,
    ScriptedModel,
    Store,
)
from fakes.agent import CannedRunner
from samples import JPEG

from jalada.modules.accounts.application.model_consent import ConsentToModels
from jalada.modules.agent.application.channels import NOTES, ChannelAssistant
from jalada.modules.agent.application.conversations import Conversations
from jalada.modules.agent.wiring import build_confirmations
from jalada.modules.evidence.application.evidence_capture import EvidenceCapture
from jalada.modules.evidence.domain.evidence import EvidenceSource
from jalada.modules.ledger.application.entry_review import EntryReview
from jalada.modules.pipeline.application.evidence_processing import EvidenceProcessor
from jalada.modules.pipeline.domain.run_types import Budget
from jalada.shared.errors import ConsentNeeded

ME = uuid.uuid4()
GEMINI = "Google's Gemini API, in the United States. It does not train on your data."


def consent(store: Store, clock: FixedClock, notice: str | None = GEMINI) -> ConsentToModels:
    return ConsentToModels(lambda: FakeUnitOfWork(store), clock, notice)


def test_without_a_model_there_is_nothing_to_agree_to(store: Store, clock: FixedClock) -> None:
    status = consent(store, clock, None).status(ME)

    assert (status.required, status.given) == (False, False)


def test_agreeing_and_withdrawing(store: Store, clock: FixedClock) -> None:
    asking = consent(store, clock)

    assert asking.status(ME).given is False
    assert asking.give(ME).given is True
    assert asking.allows(ME)
    assert store.model_consents[ME].notice == GEMINI
    assert asking.withdraw(ME).given is False
    assert not asking.allows(ME)


def test_a_new_provider_asks_everyone_again(store: Store, clock: FixedClock) -> None:
    consent(store, clock).give(ME)

    moved = consent(store, clock, "OpenAI's API, in the United States.")

    assert moved.status(ME).given is False
    assert not moved.allows(ME)


def test_a_photo_is_not_sent_to_the_model_without_agreement(
    store: Store, capture: EvidenceCapture, evidence_store: FakeEvidenceStore, clock: FixedClock
) -> None:
    model = ScriptedModel()
    processor = EvidenceProcessor(
        lambda: FakeUnitOfWork(store),
        evidence_store,
        FakeTextReader(),
        clock,
        Budget(),
        model=model,
        may_use_model=consent(store, clock).allows,
    )
    evidence = capture.capture_file(ME, JPEG, EvidenceSource.WEB_UPLOAD).evidence

    processor.process(ME, evidence.id)

    assert model.calls == [], "the photo went to rules and OCR only"


def test_the_assistant_refuses_until_the_person_agrees(store: Store, clock: FixedClock) -> None:
    asking = consent(store, clock)
    runner = CannedRunner()
    conversations = Conversations(
        lambda: FakeUnitOfWork(store), runner, clock, may_ask=asking.allows
    )

    with pytest.raises(ConsentNeeded):
        conversations.ask(ME, "How much did I pay KPLC?")
    assert runner.requests == []
    asking.give(ME)
    conversations.ask(ME, "How much did I pay KPLC?")
    assert len(runner.requests) == 1


def test_a_chat_app_says_how_to_agree(store: Store, clock: FixedClock) -> None:
    class Chat:
        notes: list[tuple[str, str]] = []

        def answer(self, chat: str, text: str, actions: object) -> None:
            raise AssertionError("no answer without agreement")

        def note(self, chat: str, text: str) -> None:
            self.notes.append((chat, text))

    def work() -> FakeUnitOfWork:
        return FakeUnitOfWork(store)

    chat = Chat()
    conversations = Conversations(work, CannedRunner(), clock, may_ask=consent(store, clock).allows)
    ChannelAssistant(
        work, conversations, build_confirmations(work, clock, EntryReview(work, clock)), chat, clock
    ).answer(ME, "42", "KPLC?")

    assert chat.notes == [("42", NOTES["consent"])]


def test_a_photo_nobody_could_read_never_reaches_the_model(
    store: Store, capture: EvidenceCapture, evidence_store: FakeEvidenceStore, clock: FixedClock
) -> None:
    class Blurred:
        def problem(self, data: bytes) -> str | None:
            return "too blurred"

    model = ScriptedModel()
    processor = EvidenceProcessor(
        lambda: FakeUnitOfWork(store),
        evidence_store,
        FakeTextReader(),
        clock,
        Budget(),
        model=model,
        photo_check=Blurred(),
    )
    evidence = capture.capture_file(ME, JPEG, EvidenceSource.WEB_UPLOAD).evidence

    processor.process(ME, evidence.id)

    assert model.calls == []
    assert store.entries == {}, "nothing was read, so the person enters it by hand"
