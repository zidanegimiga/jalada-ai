from dataclasses import dataclass
from datetime import datetime
from types import TracebackType
from typing import Any, Protocol, Self
from uuid import UUID


@dataclass(frozen=True)
class Job:
    id: int
    kind: str
    payload: dict[str, Any]
    attempts: int


class JobQueue(Protocol):
    def enqueue(self, kind: str, payload: dict[str, str]) -> None: ...
    def claim(self, now: datetime, lock_seconds: int) -> Job | None: ...
    def complete(self, job_id: int) -> None: ...
    def fail(self, job_id: int, error: str, retry_at: datetime | None) -> None: ...
    def discard_for(self, user_id: UUID) -> None: ...


class JobTransaction(Protocol):
    """The part of a unit of work the job runner needs: the queue, and committing."""

    jobs: JobQueue

    def __enter__(self) -> Self: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...
    def commit(self) -> None: ...
