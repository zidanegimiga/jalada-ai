from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Protocol


@dataclass(frozen=True)
class Answer:
    """What the server said the first time, kept so a retry gets the same."""

    status: int
    content_type: str | None
    body: bytes


class Seen(Enum):
    NEW = "new"  # First time: run it, then keep the answer.
    ANSWERED = "answered"  # Done before: send the kept answer again.
    RUNNING = "running"  # The first try has not finished.
    DIFFERENT = "different"  # The key was already used for another request.
    NO_SESSION = "no_session"  # Not signed in: nothing to keep it against.


@dataclass(frozen=True)
class Attempt:
    seen: Seen
    answer: Answer | None = None


class IdempotencyStore(Protocol):
    def begin(
        self,
        owner: str,
        key: str,
        fingerprint: str,
        now: datetime,
        expired_before: datetime,
        abandoned_before: datetime,
    ) -> Attempt: ...
    def keep(self, owner: str, key: str, answer: Answer) -> None: ...
    def drop(self, owner: str, key: str) -> None: ...
