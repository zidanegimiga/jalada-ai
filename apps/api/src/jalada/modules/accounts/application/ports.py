from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from typing import IO, TYPE_CHECKING, Protocol
from uuid import UUID

if TYPE_CHECKING:
    from jalada.modules.accounts.application.account_export import AccountData
from jalada.modules.accounts.domain.sessions import Session
from jalada.modules.accounts.domain.users import User
from jalada.modules.evidence.domain.evidence import Evidence


@dataclass(frozen=True)
class UserCredentials:
    user: User
    password_hash: str | None
    email_verified: bool = False


@dataclass(frozen=True)
class GoogleProfile:
    subject: str
    email: str
    email_verified: bool
    name: str


class UserRepository(Protocol):
    def add(
        self, user: User, password_hash: str | None, google_subject: str | None = None
    ) -> None: ...
    def get(self, user_id: UUID) -> User | None: ...
    def get_credentials(self, email: str) -> UserCredentials | None: ...
    def get_by_google_subject(self, subject: str) -> User | None: ...
    def link_google(self, user_id: UUID, subject: str, verified_at: datetime) -> None: ...
    def remove_password(self, user_id: UUID) -> None: ...
    def delete(self, user_id: UUID) -> None: ...


class SessionRepository(Protocol):
    def add(self, session: Session) -> None: ...
    def get_active(self, token_hash: str, now: datetime) -> Session | None: ...
    def delete(self, token_hash: str) -> None: ...
    def delete_all_for(self, user_id: UUID) -> None: ...


class PasswordHasher(Protocol):
    def hash(self, password: str) -> str: ...
    def verify(self, password_hash: str, password: str) -> bool: ...


class GoogleIdentity(Protocol):
    """Google's OpenID Connect sign-in. Raises GoogleSignInFailed when Google says no."""

    def authorization_url(self, state: str, nonce: str, code_verifier: str) -> str: ...
    def exchange(self, code: str, nonce: str, code_verifier: str) -> GoogleProfile: ...


class ArchiveWriter(Protocol):
    """Writes everything held about one user into a single downloadable file."""

    content_type: str
    extension: str

    def write(
        self, data: "AccountData", originals: Iterator[tuple[Evidence, bytes]], out: IO[bytes]
    ) -> None: ...
