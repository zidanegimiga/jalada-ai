import threading
from typing import Any

from jalada.modules.telegram.adapters.telegram_bot import ChatFailed
from jalada.modules.telegram.cli import poll


class ScriptedBot:
    """Gives out prepared batches of updates, then asks the poller to stop."""

    def __init__(self, stop: threading.Event, *batches: list[dict[str, Any]] | Exception) -> None:
        self._stop = stop
        self._batches = list(batches)
        self.offsets: list[int] = []

    def updates(self, offset: int, wait_seconds: int) -> list[dict[str, Any]]:
        self.offsets.append(offset)
        if not self._batches:
            self._stop.set()
            return []
        batch = self._batches.pop(0)
        if isinstance(batch, Exception):
            raise batch
        return batch


class RecordingCapture:
    def __init__(self) -> None:
        self.handled: list[dict[str, Any]] = []

    def handle(self, update: dict[str, Any]) -> None:
        self.handled.append(update)


def test_polling_hands_over_each_update_once_and_moves_the_offset_on() -> None:
    stop = threading.Event()
    bot = ScriptedBot(stop, [{"update_id": 7}, {"update_id": 8}], [{"update_id": 9}])
    capture = RecordingCapture()

    poll(bot, capture, stop)  # type: ignore[arg-type]

    assert [u["update_id"] for u in capture.handled] == [7, 8, 9]
    assert bot.offsets == [0, 9, 10]


def test_a_failed_poll_is_retried_rather_than_stopping_the_bot() -> None:
    stop = threading.Event()
    bot = ScriptedBot(stop, ChatFailed("ConnectTimeout"), [{"update_id": 1}])
    capture = RecordingCapture()
    original_wait = stop.wait
    stop.wait = lambda timeout=None: False  # type: ignore[method-assign]

    poll(bot, capture, stop)  # type: ignore[arg-type]

    stop.wait = original_wait  # type: ignore[method-assign]
    assert [u["update_id"] for u in capture.handled] == [1]
