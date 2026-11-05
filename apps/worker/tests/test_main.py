import os
import signal
import threading
from collections.abc import Iterator

import pytest
from pydantic import SecretStr

from jalada.config.settings import Settings
from jalada_worker.main import install_stop_signals, run


class IdleJobs:
    def run_one(self) -> bool:
        return False


class CountingJobs:
    """Has `pending` jobs, then nothing. Stops the worker once the queue is empty."""

    def __init__(self, pending: int, stop: threading.Event) -> None:
        self.pending = pending
        self.done = 0
        self._stop = stop

    def run_one(self) -> bool:
        if self.pending == 0:
            self._stop.set()
            return False
        self.pending -= 1
        self.done += 1
        return True


@pytest.fixture
def settings() -> Settings:
    return Settings(
        environment="test",
        database_url="postgresql+psycopg://u:p@localhost:1/unused",
        storage_access_key="access",
        storage_secret_key=SecretStr("secret"),
        evidence_keys=SecretStr("a2V5"),
    )


@pytest.fixture
def restore_signal_handlers() -> Iterator[None]:
    previous = {number: signal.getsignal(number) for number in (signal.SIGINT, signal.SIGTERM)}
    yield
    for number, handler in previous.items():
        signal.signal(number, handler)


def test_run_returns_at_once_when_already_stopped(settings: Settings) -> None:
    stop = threading.Event()
    stop.set()

    run(settings, stop, poll_interval=60, jobs=IdleJobs())


def test_run_keeps_waiting_until_stop_is_set(settings: Settings) -> None:
    stop = threading.Event()
    timer = threading.Timer(0.05, stop.set)
    timer.start()

    run(settings, stop, poll_interval=0.01, jobs=IdleJobs())

    assert stop.is_set()


def test_run_logs_start_and_stop(settings: Settings, caplog: pytest.LogCaptureFixture) -> None:
    stop = threading.Event()
    stop.set()

    with caplog.at_level("INFO", logger="jalada.worker"):
        run(settings, stop, poll_interval=60, jobs=IdleJobs())

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


def test_due_jobs_run_back_to_back_without_waiting(settings: Settings) -> None:
    stop = threading.Event()
    jobs = CountingJobs(pending=3, stop=stop)

    run(settings, stop, poll_interval=60, jobs=jobs)

    assert jobs.done == 3
