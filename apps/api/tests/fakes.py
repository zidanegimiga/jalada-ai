"""In-memory stand-ins for the ports, for fast tests without a database."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from types import TracebackType
from typing import Self
from uuid import UUID

from jalada.application.ports import SessionRepository, UserCredentials, UserRepository
from jalada.domain.sessions import Session
from jalada.domain.users import User


@dataclass
class Store:
    users: dict[UUID, UserCredentials] = field(default_factory=dict)
    sessions: dict[str, Session] = field(default_factory=dict)


class FakeUsers:
    def __init__(self, users: dict[UUID, UserCredentials]) -> None:
        self.rows = users

    def add(self, user: User, password_hash: str | None) -> None:
        self.rows[user.id] = UserCredentials(user, password_hash)

    def get(self, user_id: UUID) -> User | None:
        found = self.rows.get(user_id)
        return found.user if found else None

    def get_credentials(self, email: str) -> UserCredentials | None:
        return next((c for c in self.rows.values() if c.user.email == email), None)


class FakeSessions:
    def __init__(self, sessions: dict[str, Session]) -> None:
        self.rows = sessions

    def add(self, session: Session) -> None:
        self.rows[session.token_hash] = session

    def get_active(self, token_hash: str, now: datetime) -> Session | None:
        session = self.rows.get(token_hash)
        return session if session and session.expires_at > now else None

    def delete(self, token_hash: str) -> None:
        self.rows.pop(token_hash, None)


class FakeUnitOfWork:
    """Works on copies of the store and writes them back only on commit, like a transaction."""

    def __init__(self, store: Store) -> None:
        self._store = store

    def __enter__(self) -> Self:
        self._users = FakeUsers(dict(self._store.users))
        self._sessions = FakeSessions(dict(self._store.sessions))
        self.users: UserRepository = self._users
        self.sessions: SessionRepository = self._sessions
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        pass

    def commit(self) -> None:
        self._store.users = self._users.rows
        self._store.sessions = self._sessions.rows


class FakeHasher:
    def __init__(self) -> None:
        self.verified: list[str] = []

    def hash(self, password: str) -> str:
        return f"hashed:{password}"

    def verify(self, password_hash: str, password: str) -> bool:
        self.verified.append(password_hash)
        return password_hash == f"hashed:{password}"


class FixedClock:
    def __init__(self, now: datetime = datetime(2026, 11, 5, 9, 0, tzinfo=UTC)) -> None:
        self.current = now

    def now(self) -> datetime:
        return self.current
