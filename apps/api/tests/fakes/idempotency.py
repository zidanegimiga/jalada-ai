"""Kept answers in memory, following the same rules as the Postgres store."""

from dataclasses import dataclass
from datetime import datetime

from jalada.core.idempotency.ports import Answer, Attempt, Seen


@dataclass
class _Kept:
    fingerprint: str
    created_at: datetime
    answer: Answer | None = None


class FakeIdempotencyStore:
    def __init__(self, sessions: set[str] | None = None) -> None:
        # None: every owner counts as signed in.
        self.sessions = sessions
        self.kept: dict[tuple[str, str], _Kept] = {}

    def begin(
        self,
        owner: str,
        key: str,
        fingerprint: str,
        now: datetime,
        expired_before: datetime,
        abandoned_before: datetime,
    ) -> Attempt:
        if self.sessions is not None and owner not in self.sessions:
            return Attempt(Seen.NO_SESSION)
        found = self.kept.get((owner, key))
        if found and (
            found.created_at < expired_before
            or (found.answer is None and found.created_at < abandoned_before)
        ):
            found = None
        if found is None:
            self.kept[(owner, key)] = _Kept(fingerprint, now)
            return Attempt(Seen.NEW)
        if found.fingerprint != fingerprint:
            return Attempt(Seen.DIFFERENT)
        if found.answer is None:
            return Attempt(Seen.RUNNING)
        return Attempt(Seen.ANSWERED, found.answer)

    def keep(self, owner: str, key: str, answer: Answer) -> None:
        self.kept[(owner, key)].answer = answer

    def drop(self, owner: str, key: str) -> None:
        self.kept.pop((owner, key), None)
