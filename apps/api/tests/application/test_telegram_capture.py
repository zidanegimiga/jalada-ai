import uuid
from typing import Any

import pytest
from fakes import FakeChat, Store
from samples import JPEG, MPESA

from jalada.application.telegram_capture import REPLIES, TelegramCapture
from jalada.application.telegram_linking import TelegramLinking
from jalada.domain.evidence import EvidenceSource

USER = uuid.uuid4()
TG_USER, CHAT = 111, 222


def update(**message: Any) -> dict[str, Any]:
    return {"update_id": 1, "message": {"from": {"id": TG_USER}, "chat": {"id": CHAT}, **message}}


@pytest.fixture
def linked(linking: TelegramLinking) -> None:
    linking.link(linking.new_code(USER).code, TG_USER, CHAT)


def test_the_apps_start_link_ties_the_chat_to_the_user(
    telegram: TelegramCapture, linking: TelegramLinking, chat: FakeChat
) -> None:
    code = linking.new_code(USER).code

    telegram.handle(update(text=f"/start {code}"))

    assert linking.user_for(TG_USER) == USER
    assert chat.sent == [(CHAT, REPLIES["linked"])]


def test_a_typed_code_also_links(telegram: TelegramCapture, linking: TelegramLinking) -> None:
    code = linking.new_code(USER).code

    telegram.handle(update(text=f"  {code.lower()} "))

    assert linking.user_for(TG_USER) == USER


def test_strangers_are_told_how_to_link(
    telegram: TelegramCapture, chat: FakeChat, store: Store
) -> None:
    telegram.handle(update(text="/start"))
    telegram.handle(update(text=MPESA))

    assert [text for _, text in chat.sent] == [REPLIES["welcome"], REPLIES["not_linked"]]
    assert store.evidence == {}


def test_guessing_codes_is_slowed_down(telegram: TelegramCapture, chat: FakeChat) -> None:
    for _ in range(4):
        telegram.handle(update(text="ABCDEFGH"))

    assert [text for _, text in chat.sent] == [REPLIES["bad_code"]] * 3 + [REPLIES["too_many"]]


@pytest.mark.usefixtures("linked")
def test_a_forwarded_mpesa_message_becomes_evidence(
    telegram: TelegramCapture, chat: FakeChat, store: Store
) -> None:
    telegram.handle(update(text=MPESA))

    [evidence] = store.evidence.values()
    assert evidence.source == EvidenceSource.TELEGRAM
    assert evidence.user_id == USER
    assert chat.sent[-1] == (CHAT, REPLIES["received"])


@pytest.mark.usefixtures("linked")
def test_the_largest_photo_size_is_kept(
    telegram: TelegramCapture, chat: FakeChat, store: Store
) -> None:
    chat.files = {"small": b"tiny", "large": JPEG}
    photos = [{"file_id": "small", "file_size": 4}, {"file_id": "large", "file_size": len(JPEG)}]

    telegram.handle(update(photo=photos, caption="lunch"))
    telegram.handle(update(photo=photos))

    [evidence] = store.evidence.values()
    assert evidence.content_type == "image/jpeg"
    assert [text for _, text in chat.sent[-2:]] == [REPLIES["received"], REPLIES["already"]]


@pytest.mark.usefixtures("linked")
@pytest.mark.parametrize(
    ("message", "reply"),
    [
        ({"document": {"file_id": "d", "mime_type": "application/msword"}}, "unsupported"),
        (
            {"document": {"file_id": "d", "mime_type": "application/pdf", "file_size": 11_000_000}},
            "too_big",
        ),
        ({"photo": [{"file_id": "fake"}]}, "unsupported"),
        ({"sticker": {"file_id": "s"}}, "unsupported"),
    ],
)
def test_things_we_cannot_use_get_a_clear_reply(
    telegram: TelegramCapture, chat: FakeChat, store: Store, message: dict[str, Any], reply: str
) -> None:
    chat.files = {"fake": b"not an image"}

    telegram.handle(update(**message))

    assert chat.sent[-1] == (CHAT, REPLIES[reply])
    assert store.evidence == {}


@pytest.mark.parametrize(
    "bad", [{}, {"message": "hi"}, {"message": {"chat": {"id": 1}}}, {"edited_message": {}}]
)
def test_malformed_updates_are_ignored(
    telegram: TelegramCapture, chat: FakeChat, bad: dict[str, Any]
) -> None:
    telegram.handle(bad)

    assert chat.sent == []
