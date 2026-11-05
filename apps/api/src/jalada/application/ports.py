from dataclasses import dataclass
from datetime import datetime
from types import TracebackType
from typing import Protocol, Self
from uuid import UUID

from jalada.domain.evidence import Evidence
from jalada.domain.sessions import Session
from jalada.domain.users import User


@dataclass(frozen=True)
class UserCredentials:
    user: User
    password_hash: str | None


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
    def link_google(self, user_id: UUID, subject: str) -> None: ...


class SessionRepository(Protocol):
    def add(self, session: Session) -> None: ...
    def get_active(self, token_hash: str, now: datetime) -> Session | None: ...
    def delete(self, token_hash: str) -> None: ...


class EvidenceRepository(Protocol):
    """Evidence for one user. Every query is limited to that user."""

    def add(self, evidence: Evidence) -> None: ...
    def get(self, evidence_id: UUID) -> Evidence | None: ...
    def get_by_fingerprint(self, sha256: str) -> Evidence | None: ...
    def list_recent(self, limit: int) -> list[Evidence]: ...


class JobQueue(Protocol):
    def enqueue(self, kind: str, payload: dict[str, str]) -> None: ...


class UnitOfWork(Protocol):
    """One database transaction. Nothing is saved unless `commit` is called."""

    users: UserRepository
    sessions: SessionRepository
    jobs: JobQueue

    def evidence_for(self, user_id: UUID) -> EvidenceRepository: ...

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


class GoogleIdentity(Protocol):
    """Google's OpenID Connect sign-in. Raises GoogleSignInFailed when Google says no."""

    def authorization_url(self, state: str, nonce: str, code_verifier: str) -> str: ...
    def exchange(self, code: str, nonce: str, code_verifier: str) -> GoogleProfile: ...


class EvidenceStore(Protocol):
    """Keeps the original bytes of each piece of evidence, encrypted at rest."""

    key_id: str

    def put(self, evidence_id: UUID, user_id: UUID, data: bytes) -> None: ...
    def get(self, evidence_id: UUID, user_id: UUID, key_id: str) -> bytes: ...
    def delete(self, evidence_id: UUID, user_id: UUID) -> None: ...


class Clock(Protocol):
    def now(self) -> datetime: ...
