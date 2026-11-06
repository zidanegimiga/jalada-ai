import logging
from typing import Any
from uuid import UUID

from jalada.core.ports import Limiter
from jalada.modules.evidence.application.evidence_capture import Captured, EvidenceCapture
from jalada.modules.evidence.domain.evidence import MAX_FILE_BYTES, EvidenceSource
from jalada.modules.telegram.application.ports import ChatChannel
from jalada.modules.telegram.application.telegram_linking import TelegramLinking
from jalada.modules.telegram.application.telegram_messages import TelegramMessage, read_message
from jalada.modules.telegram.domain.telegram import CODE_ALPHABET, CODE_LENGTH
from jalada.shared.errors import EmptyEvidence, FileTooLarge, UnsupportedFile

logger = logging.getLogger("jalada.telegram")

REPLIES = {
    "welcome": "Hello. To send receipts here, link this chat to Jalada AI: open the app, "
    "tap Link Telegram, and send me the code it shows.",
    "linked": "Linked. Send me receipts, PDFs or forwarded M-Pesa messages.",
    "bad_code": "That code did not work. Codes last 10 minutes; ask the app for a new one.",
    "not_linked": "This chat is not linked yet. Open Jalada AI, tap Link Telegram, and send "
    "me the code it shows.",
    "received": "Got it. I will tell you what I find.",
    "already": "You already sent this one.",
    "unsupported": "I can read photos, PDFs and text messages. Try one of those.",
    "too_big": "That file is too big. Files can be up to 10 MB.",
    "too_many": "That is a lot at once. Wait a little and try again.",
}


class TelegramCapture:
    """Turns what users send the bot into evidence, and answers them."""

    def __init__(
        self,
        linking: TelegramLinking,
        capture: EvidenceCapture,
        bot: ChatChannel,
        link_limiter: Limiter,
        upload_limiter: Limiter,
    ) -> None:
        self._linking = linking
        self._capture = capture
        self._bot = bot
        self._link_limiter = link_limiter
        self._upload_limiter = upload_limiter

    def handle(self, update: dict[str, Any]) -> None:
        message = read_message(update)
        if message is None:
            return
        user_id = self._linking.user_for(message.telegram_user_id)
        code = _code_in(message.text)
        if code is not None or user_id is None:
            self._reply(message, self._link(message, code))
        else:
            self._reply(message, self._store(message, user_id))

    def _link(self, message: TelegramMessage, code: str | None) -> str:
        if code is None:
            return "welcome" if (message.text or "").startswith("/start") else "not_linked"
        if not self._link_limiter.allow(f"telegram-link:{message.telegram_user_id}"):
            return "too_many"
        linked = self._linking.link(code, message.telegram_user_id, message.chat_id)
        return "linked" if linked else "bad_code"

    def _store(self, message: TelegramMessage, user_id: UUID) -> str:
        if message.unsupported_file:
            return "unsupported"
        if not self._upload_limiter.allow(f"user:{user_id}"):
            return "too_many"
        try:
            captured = self._captured(message, user_id)
        except (UnsupportedFile, EmptyEvidence):
            return "unsupported"
        except FileTooLarge:
            return "too_big"
        return "already" if captured.duplicate else "received"

    def _captured(self, message: TelegramMessage, user_id: UUID) -> Captured:
        if message.file_id:
            if (message.file_size or 0) > MAX_FILE_BYTES:
                raise FileTooLarge
            data = self._bot.download(message.file_id, MAX_FILE_BYTES)
            if data is None:
                raise FileTooLarge
            return self._capture.capture_file(user_id, data, EvidenceSource.TELEGRAM)
        return self._capture.capture_text(user_id, message.text or "", EvidenceSource.TELEGRAM)

    def _reply(self, message: TelegramMessage, key: str) -> None:
        """A failed reply is logged, not raised: the evidence is already saved, and an error
        here would make Telegram send the same message again."""
        try:
            self._bot.send(message.chat_id, REPLIES[key])
        except Exception as error:
            logger.warning("replying on Telegram failed with %s", type(error).__name__)


def _code_in(text: str | None) -> str | None:
    """A link code, from "/start CODE" (the app's link) or the code typed on its own."""
    words = (text or "").strip().split()
    if words[:1] == ["/start"]:
        words = words[1:]
    if len(words) != 1:
        return None
    candidate = words[0].upper()
    if len(candidate) == CODE_LENGTH and set(candidate) <= set(CODE_ALPHABET):
        return candidate
    return None
