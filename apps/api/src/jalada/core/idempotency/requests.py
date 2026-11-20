import hashlib
import re
from datetime import timedelta

from jalada.core.idempotency.ports import Answer, Attempt, IdempotencyStore
from jalada.core.ports import Clock

# Answers are kept a day: long enough for a laptop that was offline overnight to retry.
KEEP_ANSWERS = timedelta(hours=24)
# A first try still running after this is taken to have died with its server.
GIVE_UP_RUNNING = timedelta(minutes=2)
VALID_KEY = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def owner_of(session_token: str) -> str:
    """The same hash the sessions table keeps, so kept answers go when the session does."""
    return hashlib.sha256(session_token.encode()).hexdigest()


def fingerprint_of(method: str, path: str, query: bytes, body: bytes) -> str:
    digest = hashlib.sha256()
    for part in (method.encode(), path.encode(), query, body):
        digest.update(len(part).to_bytes(8, "big"))
        digest.update(part)
    return digest.hexdigest()


class IdempotentRequests:
    """A write sent twice with the same Idempotency-Key is applied once (decision 0029)."""

    def __init__(
        self,
        store: IdempotencyStore,
        clock: Clock,
        keep: timedelta = KEEP_ANSWERS,
        give_up: timedelta = GIVE_UP_RUNNING,
    ) -> None:
        self._store = store
        self._clock = clock
        self._keep = keep
        self._give_up = give_up

    def begin(self, owner: str, key: str, fingerprint: str) -> Attempt:
        now = self._clock.now()
        return self._store.begin(
            owner, key, fingerprint, now, now - self._keep, now - self._give_up
        )

    def finish(self, owner: str, key: str, answer: Answer) -> None:
        # A server failure is not an answer: the retry should run it again.
        if answer.status >= 500:
            self._store.drop(owner, key)
        else:
            self._store.keep(owner, key, answer)

    def abandon(self, owner: str, key: str) -> None:
        self._store.drop(owner, key)
