from dataclasses import dataclass
from datetime import datetime
from types import TracebackType
from typing import Protocol, Self
from uuid import UUID

from jalada.domain.sessions import Session
from jalada.domain.users import User


@dataclass(frozen=True)
class UserCredentials:
    user: User
    password_hash: str | None


class UserRepository(Protocol):
    def add(self, user: User, password_hash: str | None) -> None: ...
    def get(self, user_id: UUID) -> User | None: ...
    def get_credentials(self, email: str) -> UserCredentials | None: ...


class SessionRepository(Protocol):
    def add(self, session: Session) -> None: ...
    def get_active(self, token_hash: str, now: datetime) -> Session | None: ...
    def delete(self, token_hash: str) -> None: ...


class UnitOfWork(Protocol):
    """One database transaction. Nothing is saved unless `commit` is called."""

    users: UserRepository
    sessions: SessionRepository

    def __enter__(self) -> Self: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...
    def commit(self) -> None: ...


class PasswordHasher(Protocol):
    def hash(self, password: str) -> str: ...
    def verify(self, password_hash: str, password: str) -> bool: ...


class Clock(Protocol):
    def now(self) -> datetime: ...
