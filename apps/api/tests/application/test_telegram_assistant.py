"""Asking the assistant from Telegram, and answering its suggestions with buttons."""

import uuid
from datetime import UTC, datetime
from typing import Any

import pytest
from fakes import FakeChat, Store
from samples import MPESA

from jalada.modules.agent.domain.proposals import ActionKind, ActionStatus, ProposedAction
from jalada.modules.evidence.application.evidence_capture import EvidenceCapture
from jalada.modules.telegram.adapters.assistant_replies import TelegramReplies
from jalada.modules.telegram.application.telegram_capture import REPLIES, TelegramCapture
from jalada.modules.telegram.application.telegram_linking import TelegramLinking
from jalada.shared.http.rate_limit import RateLimiter

USER = uuid.uuid4()
TG_USER, CHAT = 111, 222
ACTION = uuid.uuid4()


class Desk:
    """Records what Telegram hands the assistant."""

    def __init__(self) -> None:
        self.questions: list[tuple[uuid.UUID, str, str]] = []
        self.decisions: list[tuple[uuid.UUID, str, uuid.UUID, bool]] = []

    def queue(self, user_id: uuid.UUID, chat: str, question: str) -> None:
        self.questions.append((user_id, chat, question))

    def decide(self, user_id: uuid.UUID, chat: str, action_id: uuid.UUID, confirm: bool) -> None:
        self.decisions.append((user_id, chat, action_id, confirm))


def message(text: str) -> dict[str, Any]:
    return {"message": {"from": {"id": TG_USER}, "chat": {"id": CHAT}, "text": text}}


def tap(data: str, sender: int = TG_USER) -> dict[str, Any]:
    return {
        "callback_query": {
            "id": "tap-1",
            "from": {"id": sender},
            "message": {"chat": {"id": CHAT}},
            "data": data,
        }
    }


@pytest.fixture
def desk() -> Desk:
    return Desk()


@pytest.fixture
def bot(
    linking: TelegramLinking, capture: EvidenceCapture, chat: FakeChat, desk: Desk
) -> TelegramCapture:
    linking.link(linking.new_code(USER).code, TG_USER, CHAT)
    limit = RateLimiter("100/minute")
    return TelegramCapture(linking, capture, chat, limit, limit, desk)


@pytest.mark.parametrize(
    ("text", "question"),
    [
        ("How much did I pay KPLC this year?", "How much did I pay KPLC this year?"),
        ("/ask what is waiting for me", "what is waiting for me"),
    ],
)
def test_a_question_goes_to_the_assistant_not_the_ledger(
    bot: TelegramCapture, desk: Desk, chat: FakeChat, store: Store, text: str, question: str
) -> None:
    bot.handle(message(text))

    assert desk.questions == [(USER, str(CHAT), question)]
    assert chat.sent == [(CHAT, REPLIES["asking"])]
    assert store.evidence == {}


def test_a_forwarded_mpesa_message_is_still_evidence(
    bot: TelegramCapture, desk: Desk, store: Store
) -> None:
    bot.handle(message(MPESA))

    assert desk.questions == []
    assert len(store.evidence) == 1


def test_with_the_assistant_off_a_question_is_kept_as_a_note(
    telegram: TelegramCapture, linking: TelegramLinking, store: Store
) -> None:
    linking.link(linking.new_code(USER).code, TG_USER, CHAT)

    telegram.handle(message("Lunch with a client, Ksh 1,200 cash?"))

    assert len(store.evidence) == 1


def test_a_tap_on_confirm_decides_the_change(
    bot: TelegramCapture, desk: Desk, chat: FakeChat
) -> None:
    bot.handle(tap(f"agent:confirm:{ACTION}"))

    assert desk.decisions == [(USER, str(CHAT), ACTION, True)]
    assert chat.taps_answered == ["tap-1"]


def test_a_tap_on_not_now_declines(bot: TelegramCapture, desk: Desk) -> None:
    bot.handle(tap(f"agent:decline:{ACTION}"))

    assert desk.decisions == [(USER, str(CHAT), ACTION, False)]


@pytest.mark.parametrize(
    "data", ["agent:delete:" + str(ACTION), "agent:confirm:not-an-id", "other", "agent:confirm"]
)
def test_a_tap_that_is_not_ours_does_nothing(
    bot: TelegramCapture, desk: Desk, chat: FakeChat, data: str
) -> None:
    bot.handle(tap(data))

    assert desk.decisions == []
    assert chat.taps_answered == ["tap-1"], "the button still stops spinning"


def test_a_tap_from_an_unlinked_account_does_nothing(bot: TelegramCapture, desk: Desk) -> None:
    bot.handle(tap(f"agent:confirm:{ACTION}", sender=999))

    assert desk.decisions == []


def test_suggestions_arrive_under_the_answer_with_buttons() -> None:
    chat = FakeChat()
    action = ProposedAction(
        ACTION,
        USER,
        uuid.uuid4(),
        uuid.uuid4(),
        ActionKind.CHANGE_CATEGORY,
        {},
        "Move Ksh 2,500.00 to KPLC PREPAID to Workspace rent",
        ActionStatus.PROPOSED,
        datetime(2026, 11, 18, tzinfo=UTC),
    )

    TelegramReplies(chat).answer(str(CHAT), "I suggested a change.", [action])

    assert chat.sent == [(CHAT, "I suggested a change.")]
    assert chat.buttons == [
        (
            CHAT,
            "Move Ksh 2,500.00 to KPLC PREPAID to Workspace rent",
            [("Confirm", f"agent:confirm:{ACTION}"), ("Not now", f"agent:decline:{ACTION}")],
        )
    ]
