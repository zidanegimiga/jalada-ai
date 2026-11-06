import secrets
import uuid
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime, timedelta

from jalada.application.errors import (
    EmailAlreadyRegistered,
    GoogleSignInFailed,
    InvalidCredentials,
    NotSignedIn,
    WeakPassword,
)
from jalada.application.ports import (
    Clock,
    GoogleProfile,
    PasswordHasher,
    UnitOfWork,
    UserCredentials,
)
from jalada.domain.sessions import Session, hash_session_token
from jalada.domain.users import User, is_acceptable_password, normalize_email


@dataclass(frozen=True)
class IssuedSession:
    token: str
    user: User
    expires_at: datetime
    # True when Google sign-in took over an account whose password nobody had proven.
    password_removed: bool = False


class Authenticator:
    """Sign-up, sign-in, sign-out, and finding the user behind a session token."""

    def __init__(
        self,
        unit_of_work: Callable[[], UnitOfWork],
        hasher: PasswordHasher,
        clock: Clock,
        session_lifetime: timedelta,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._hasher = hasher
        self._clock = clock
        self._session_lifetime = session_lifetime
        # Checked against when the email is unknown, so both failures take the same time.
        self._decoy_hash = hasher.hash(secrets.token_urlsafe(16))

    def sign_up(self, email: str, password: str, display_name: str) -> IssuedSession:
        if not is_acceptable_password(password):
            raise WeakPassword
        email = normalize_email(email)
        with self._unit_of_work() as work:
            if work.users.get_credentials(email) is not None:
                raise EmailAlreadyRegistered
            user = User(uuid.uuid4(), email, display_name.strip(), self._clock.now())
            work.users.add(user, self._hasher.hash(password))
            issued = self._start_session(work, user)
            work.commit()
        return issued

    def sign_in(self, email: str, password: str) -> IssuedSession:
        with self._unit_of_work() as work:
            credentials = work.users.get_credentials(normalize_email(email))
            stored_hash = credentials.password_hash if credentials else None
            matches = self._hasher.verify(stored_hash or self._decoy_hash, password)
            if credentials is None or stored_hash is None or not matches:
                raise InvalidCredentials
            issued = self._start_session(work, credentials.user)
            work.commit()
        return issued

    def sign_in_with_google(self, profile: GoogleProfile) -> IssuedSession:
        """Match by Google id, else link the account with the same verified email, else create."""
        if not profile.email_verified:
            raise GoogleSignInFailed
        email = normalize_email(profile.email)
        password_removed = False
        with self._unit_of_work() as work:
            user = work.users.get_by_google_subject(profile.subject)
            credentials = None if user else work.users.get_credentials(email)
            if credentials:
                user = credentials.user
                password_removed = self._link_google(work, credentials, profile.subject)
            elif user is None:
                name = (profile.name.strip() or email.split("@")[0])[:80]
                user = User(uuid.uuid4(), email, name, self._clock.now())
                work.users.add(user, None, google_subject=profile.subject)
            issued = self._start_session(work, user)
            work.commit()
        return replace(issued, password_removed=password_removed)

    def _link_google(self, work: UnitOfWork, credentials: UserCredentials, subject: str) -> bool:
        """Link Google to an account with the same email. True if its password was removed.

        Nobody has proven they own the email of an account made with a password, so whoever
        made it may not be this Google user. Anything they could still use is removed: the
        password, every session and the Telegram link.
        """
        user_id = credentials.user.id
        if not credentials.email_verified:
            work.users.remove_password(user_id)
            work.sessions.delete_all_for(user_id)
            work.telegram.unlink(user_id)
        work.users.link_google(user_id, subject, self._clock.now())
        return not credentials.email_verified and credentials.password_hash is not None

    def sign_out(self, token: str) -> None:
        with self._unit_of_work() as work:
            work.sessions.delete(hash_session_token(token))
            work.commit()

    def current_user(self, token: str) -> User:
        with self._unit_of_work() as work:
            session = work.sessions.get_active(hash_session_token(token), self._clock.now())
            user = work.users.get(session.user_id) if session else None
        if user is None:
            raise NotSignedIn
        return user

    def _start_session(self, work: UnitOfWork, user: User) -> IssuedSession:
        token = secrets.token_urlsafe(32)
        expires_at = self._clock.now() + self._session_lifetime
        work.sessions.add(Session(hash_session_token(token), user.id, expires_at))
        return IssuedSession(token, user, expires_at)
