import secrets
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from jalada.core.ports import Clock
from jalada.modules.accounts.application.authentication import IssuedSession
from jalada.modules.accounts.domain.device_codes import (
    CHALLENGE,
    DeviceCode,
    verifier_matches,
)
from jalada.modules.accounts.domain.sessions import hash_session_token, new_session
from jalada.shared.errors import DeviceSignInFailed
from jalada.unit_of_work import UnitOfWork

# Long enough to switch back from the browser, short enough that a stray code soon expires.
CODE_LIFETIME = timedelta(minutes=2)


@dataclass(frozen=True)
class IssuedCode:
    code: str
    expires_at: datetime


class DeviceSignIn:
    """Signs the desktop app in through the browser, where the person is already signed in
    with whatever they use there: a password, Google, and later a passkey (decision 0029)."""

    def __init__(
        self,
        unit_of_work: Callable[[], UnitOfWork],
        clock: Clock,
        session_lifetime: timedelta,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._session_lifetime = session_lifetime

    def issue_code(self, user_id: UUID, challenge: str) -> IssuedCode:
        """A one-time code for the signed-in person, bound to the app's challenge."""
        if not CHALLENGE.match(challenge):
            raise DeviceSignInFailed
        code = secrets.token_urlsafe(32)
        expires_at = self._clock.now() + CODE_LIFETIME
        with self._unit_of_work() as work:
            work.device_codes.add(
                DeviceCode(hash_session_token(code), user_id, challenge, expires_at)
            )
            work.commit()
        return IssuedCode(code, expires_at)

    def exchange(self, code: str, verifier: str) -> IssuedSession:
        """A session for the app that holds both the code and the verifier. The code is used
        up by the first try, right or wrong, so a verifier cannot be guessed at."""
        with self._unit_of_work() as work:
            found = work.device_codes.take(hash_session_token(code), self._clock.now())
            user = work.users.get(found.user_id) if found else None
            if found is None or user is None or not verifier_matches(verifier, found.challenge):
                work.commit()
                raise DeviceSignInFailed
            token, session = new_session(user.id, self._clock.now(), self._session_lifetime)
            work.sessions.add(session)
            work.commit()
        return IssuedSession(token, user, session.expires_at)
