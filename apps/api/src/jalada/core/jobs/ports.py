from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol
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
