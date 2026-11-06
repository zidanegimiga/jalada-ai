import logging
from typing import Any

import pytest
from fakes import FakeUnitOfWork, FixedClock, Store, later

from jalada.application.job_runner import JobRunner
from jalada.application.ports import Job


class Handler:
    def __init__(self, fail_times: int = 0) -> None:
        self.fail_times = fail_times
        self.handled: list[dict[str, Any]] = []
        self.gave_up: list[dict[str, Any]] = []

    def handle(self, payload: dict[str, Any]) -> None:
        if self.fail_times:
            self.fail_times -= 1
            raise ConnectionError("storage is down for Ksh 1,000 receipt")
        self.handled.append(payload)

    def give_up(self, payload: dict[str, Any]) -> None:
        self.gave_up.append(payload)


def runner_with(store: Store, clock: FixedClock, handler: Handler) -> JobRunner:
    store.queue[1] = [Job(1, "work", {"n": "1"}, 0), "queued", clock.now()]
    return JobRunner(lambda: FakeUnitOfWork(store), {"work": handler}, clock)


def test_a_due_job_runs_once_and_is_done(store: Store, clock: FixedClock) -> None:
    handler = Handler()
    runner = runner_with(store, clock, handler)

    assert runner.run_one() is True
    assert runner.run_one() is False
    assert handler.handled == [{"n": "1"}]
    assert store.queue[1][1] == "done"


def test_a_failed_job_waits_longer_after_each_failure(store: Store, clock: FixedClock) -> None:
    handler = Handler(fail_times=2)
    runner = runner_with(store, clock, handler)

    runner.run_one()
    assert store.queue[1][1:] == ["queued", later(clock, 2)]
    assert runner.run_one() is False, "not due yet"

    clock.current = later(clock, 2)
    runner.run_one()
    assert store.queue[1][1:] == ["queued", later(clock, 4)]

    clock.current = later(clock, 4)
    runner.run_one()
    assert store.queue[1][1] == "done"


def test_after_three_failures_the_handler_gives_up(store: Store, clock: FixedClock) -> None:
    handler = Handler(fail_times=5)
    runner = runner_with(store, clock, handler)

    for _ in range(3):
        runner.run_one()
        clock.current = later(clock, 60)

    assert store.queue[1][1] == "failed"
    assert handler.gave_up == [{"n": "1"}]


def test_a_failing_give_up_does_not_stop_the_runner(store: Store, clock: FixedClock) -> None:
    class BrokenGiveUp(Handler):
        def give_up(self, payload: dict[str, Any]) -> None:
            raise KeyError("user_id")

    runner = runner_with(store, clock, BrokenGiveUp(fail_times=5))

    for _ in range(3):
        assert runner.run_one() is True
        clock.current = later(clock, 60)

    assert store.queue[1][1] == "failed"


def test_a_failure_is_logged_with_the_job_and_its_type_only(
    store: Store, clock: FixedClock, caplog: pytest.LogCaptureFixture
) -> None:
    runner = runner_with(store, clock, Handler(fail_times=1))

    with caplog.at_level(logging.ERROR, logger="jalada.jobs"):
        runner.run_one()

    [record] = caplog.records
    assert record.getMessage() == "job failed with ConnectionError, will retry"
    assert record.exc_info is not None, "the stack goes to the log formatter and error tracking"
    assert "Ksh" not in record.getMessage()
