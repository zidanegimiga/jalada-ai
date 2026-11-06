import json

import httpx2
import pytest

from jalada.modules.telegram.adapters.telegram_bot import API, ChatFailed, TelegramBot

TOKEN = "123:secret-token"


def bot_with(handler: object, seen: list[httpx2.Request]) -> TelegramBot:
    def record(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        return handler(request)  # type: ignore[operator, no-any-return]

    return TelegramBot(TOKEN, httpx2.Client(transport=httpx2.MockTransport(record), base_url=API))


def ok(result: object) -> httpx2.Response:
    return httpx2.Response(200, json={"ok": True, "result": result})


def test_sending_a_message() -> None:
    seen: list[httpx2.Request] = []

    bot_with(lambda r: ok({}), seen).send(222, "Got it.")

    assert seen[0].url.path == f"/bot{TOKEN}/sendMessage"
    assert json.loads(seen[0].content) == {"chat_id": 222, "text": "Got it."}


def test_downloading_a_file_in_two_steps() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        if request.url.path.endswith("/getFile"):
            return ok({"file_path": "photos/file_1.jpg", "file_size": 3})
        return httpx2.Response(200, content=b"jpg")

    seen: list[httpx2.Request] = []

    assert bot_with(handler, seen).download("abc", max_bytes=10) == b"jpg"
    assert seen[1].url.path == f"/file/bot{TOKEN}/photos/file_1.jpg"


def test_files_over_the_limit_are_not_downloaded() -> None:
    seen: list[httpx2.Request] = []
    bot = bot_with(lambda r: ok({"file_path": "big.pdf", "file_size": 50}), seen)

    assert bot.download("abc", max_bytes=10) is None
    assert len(seen) == 1, "the file itself was never fetched"


@pytest.mark.parametrize(
    "response",
    [
        httpx2.Response(401, json={"ok": False, "description": "Unauthorized"}),
        httpx2.Response(200, json={"ok": False}),
        httpx2.Response(200, content=b"not json"),
    ],
)
def test_failures_never_reveal_the_token(response: httpx2.Response) -> None:
    with pytest.raises(ChatFailed) as failure:
        bot_with(lambda r: response, []).send(1, "x")

    assert TOKEN not in str(failure.value)
    assert failure.value.__cause__ is None
