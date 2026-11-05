"""Reading the few fields we use from a Telegram update. Updates are untrusted input."""

from dataclasses import dataclass
from typing import Any

ACCEPTED_DOCUMENTS = {"application/pdf", "image/jpeg", "image/png", "image/webp"}


@dataclass(frozen=True)
class TelegramMessage:
    telegram_user_id: int
    chat_id: int
    text: str | None
    file_id: str | None
    file_size: int | None
    # True for a document of a type we do not accept, such as a Word file.
    unsupported_file: bool = False


def read_message(update: dict[str, Any]) -> TelegramMessage | None:
    message = update.get("message")
    if not isinstance(message, dict):
        return None
    sender, chat = message.get("from"), message.get("chat")
    if not (isinstance(sender, dict) and isinstance(chat, dict)):
        return None
    user_id, chat_id = sender.get("id"), chat.get("id")
    if not (isinstance(user_id, int) and isinstance(chat_id, int)):
        return None
    text = message.get("text") or message.get("caption")
    file_id, size, unsupported = _file(message)
    return TelegramMessage(
        user_id, chat_id, text if isinstance(text, str) else None, file_id, size, unsupported
    )


def _file(message: dict[str, Any]) -> tuple[str | None, int | None, bool]:
    photos = message.get("photo")
    if isinstance(photos, list) and photos:
        # Telegram sends several sizes of the same photo; the last is the largest.
        largest = photos[-1] if isinstance(photos[-1], dict) else {}
        return _id(largest), _size(largest), False
    document = message.get("document")
    if isinstance(document, dict):
        if document.get("mime_type") not in ACCEPTED_DOCUMENTS:
            return None, None, True
        return _id(document), _size(document), False
    return None, None, False


def _id(item: dict[str, Any]) -> str | None:
    value = item.get("file_id")
    return value if isinstance(value, str) else None


def _size(item: dict[str, Any]) -> int | None:
    value = item.get("file_size")
    return value if isinstance(value, int) else None
