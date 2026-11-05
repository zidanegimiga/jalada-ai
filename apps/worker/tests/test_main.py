import os
import signal
import threading
from collections.abc import Iterator

import pytest

from jalada.config.settings import Settings
from jalada_worker.main import install_stop_signals, run


@pytest.fixture
def settings() -> Settings:
    return Settings(environment="test")


@pytest.fixture
def restore_signal_handlers() -> Iterator[None]:
    previous = {number: signal.getsignal(number) for number in (signal.SIGINT, signal.SIGTERM)}
    yield
    for number, handler in previous.items():
        signal.signal(number, handler)


def test_run_returns_at_once_when_already_stopped(settings: Settings) -> None:
    stop = threading.Event()
    stop.set()

    run(settings, stop, poll_interval=60)


def test_run_keeps_waiting_until_stop_is_set(settings: Settings) -> None:
    stop = threading.Event()
    timer = threading.Timer(0.05, stop.set)
    timer.start()

    run(settings, stop, poll_interval=0.01)

    assert stop.is_set()


def test_run_logs_start_and_stop(settings: Settings, caplog: pytest.LogCaptureFixture) -> None:
    stop = threading.Event()
    stop.set()

    with caplog.at_level("INFO", logger="jalada.worker"):
        run(settings, stop, poll_interval=60)

    assert caplog.messages == ["worker started in test", "worker stopped"]


@pytest.mark.usefixtures("restore_signal_handlers")
@pytest.mark.parametrize(
    "signal_number", [signal.SIGINT, signal.SIGTERM], ids=["SIGINT", "SIGTERM"]
)
def test_shutdown_signals_set_the_stop_event(signal_number: int) -> None:
    stop = threading.Event()
    install_stop_signals(stop)

    os.kill(os.getpid(), signal_number)

    assert stop.wait(1)
