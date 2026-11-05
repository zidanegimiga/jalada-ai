import logging
import threading
from collections.abc import Callable
from datetime import timedelta
from typing import Any, Protocol

from jalada.application.ports import Clock, UnitOfWork

logger = logging.getLogger("jalada.jobs")

LOCK_SECONDS = 300
MAX_ATTEMPTS = 3


class JobHandler(Protocol):
    def handle(self, payload: dict[str, Any]) -> None: ...
    def give_up(self, payload: dict[str, Any]) -> None: ...


class JobRunner:
    """Claims one job at a time and retries failures with growing gaps."""

    def __init__(
        self,
        unit_of_work: Callable[[], UnitOfWork],
        handlers: dict[str, JobHandler],
        clock: Clock,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._handlers = handlers
        self._clock = clock

    def run_one(self) -> bool:
        """Run the next due job. False when there was nothing to do."""
        with self._unit_of_work() as work:
            job = work.jobs.claim(self._clock.now(), LOCK_SECONDS)
            work.commit()
        if job is None:
            return False
        handler = self._handlers[job.kind]
        try:
            handler.handle(job.payload)
        except Exception as error:
            final = job.attempts >= MAX_ATTEMPTS
            retry_at = None if final else self._clock.now() + timedelta(minutes=2**job.attempts)
            with self._unit_of_work() as work:
                # Only the error type is kept: messages can contain financial content.
                work.jobs.fail(job.id, type(error).__name__, retry_at)
                work.commit()
            if final:
                self._give_up(handler, job.id, job.payload)
            return True
        with self._unit_of_work() as work:
            work.jobs.complete(job.id)
            work.commit()
        return True

    @staticmethod
    def _give_up(handler: JobHandler, job_id: int, payload: dict[str, Any]) -> None:
        """A broken give-up must not stop the worker from taking the next job."""
        try:
            handler.give_up(payload)
        except Exception as error:
            logger.error("giving up on job %s failed with %s", job_id, type(error).__name__)


class Runs(Protocol):
    def run_one(self) -> bool: ...


def work_until(stop: threading.Event, jobs: Runs, poll_interval: float) -> None:
    """Run due jobs back to back, and wait between polls when there are none."""
    while not stop.is_set():
        if not jobs.run_one():
            stop.wait(poll_interval)
