from typing import Any

import httpx2

API = "https://api.telegram.org"


class ChatFailed(Exception):
    """Telegram could not be reached or refused the call."""


class TelegramBot:
    """The Telegram Bot API over plain HTTP.

    The bot token is part of every address, so addresses are never logged and errors carry
    only their type.
    """

    def __init__(self, token: str, client: httpx2.Client | None = None) -> None:
        self._token = token
        self._client = client or httpx2.Client(base_url=API, timeout=30)

    def send(self, chat_id: int, text: str) -> None:
        self._call("sendMessage", {"chat_id": chat_id, "text": text})

    def send_with_buttons(self, chat_id: int, text: str, buttons: list[tuple[str, str]]) -> None:
        """A message with one row of buttons. Each is (label, data sent back when tapped)."""
        keyboard = [[{"text": label, "callback_data": data} for label, data in buttons]]
        self._call(
            "sendMessage",
            {"chat_id": chat_id, "text": text, "reply_markup": {"inline_keyboard": keyboard}},
        )

    def answer_tap(self, tap_id: str) -> None:
        """Tells Telegram a button tap was received, so the button stops spinning."""
        self._call("answerCallbackQuery", {"callback_query_id": tap_id})

    def download(self, file_id: str, max_bytes: int) -> bytes | None:
        """The file's bytes, or None when it is bigger than `max_bytes`."""
        info = self._call("getFile", {"file_id": file_id})
        if not isinstance(info, dict):
            return None
        size, path = info.get("file_size"), info.get("file_path")
        if not isinstance(path, str) or (isinstance(size, int) and size > max_bytes):
            return None
        try:
            response = self._client.get(f"/file/bot{self._token}/{path}")
            response.raise_for_status()
        except httpx2.HTTPError as error:
            raise ChatFailed(type(error).__name__) from None
        return response.content if len(response.content) <= max_bytes else None

    def set_webhook(self, url: str, secret: str) -> None:
        self._call(
            "setWebhook",
            {
                "url": url,
                "secret_token": secret,
                # Taps on the assistant's Confirm and Not now buttons arrive as callback queries.
                "allowed_updates": ["message", "callback_query"],
            },
        )

    def updates(self, offset: int, wait_seconds: int) -> list[dict[str, Any]]:
        """New messages by long polling, for local work without a public address."""
        result = self._call("getUpdates", {"offset": offset, "timeout": wait_seconds})
        if not isinstance(result, list):
            return []
        return [update for update in result if isinstance(update, dict)]

    def _call(self, method: str, body: dict[str, object]) -> object:
        """The call's result, which callers check the shape of themselves."""
        try:
            response = self._client.post(f"/bot{self._token}/{method}", json=body, timeout=60)
            response.raise_for_status()
            payload = response.json()
        except (httpx2.HTTPError, ValueError) as error:
            # "from None" drops the original error, whose message would include the address.
            raise ChatFailed(type(error).__name__) from None
        if not payload.get("ok"):
            raise ChatFailed("NotOk")
        return payload.get("result")
