from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from types import TracebackType
from typing import Any, Protocol, Self
from uuid import UUID

from jalada.domain.entries import Entry
from jalada.domain.evidence import Evidence, EvidenceKind, EvidenceStatus
from jalada.domain.sessions import Session
from jalada.domain.users import User
from jalada.pipeline.classifier import Preference
from jalada.pipeline.process import StepRecord


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
    def set_outcome(
        self, evidence_id: UUID, kind: EvidenceKind, status: EvidenceStatus
    ) -> None: ...


class EntryRepository(Protocol):
    """Ledger entries for one user."""

    def add(self, entry: Entry) -> None: ...
    def has_mpesa_code(self, code: str) -> bool: ...
    def has_certificate_serial(self, serial: str) -> bool: ...


class PreferenceRepository(Protocol):
    def all(self) -> dict[str, Preference]: ...


@dataclass(frozen=True)
class PipelineRun:
    id: UUID
    user_id: UUID
    evidence_id: UUID
    outcome: str
    attempts: int
    input_tokens: int
    output_tokens: int
    cost_usd: Decimal
    started_at: datetime
    finished_at: datetime


class RunRepository(Protocol):
    def add(self, run: PipelineRun, steps: list[StepRecord]) -> None: ...


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


class UnitOfWork(Protocol):
    """One database transaction. Nothing is saved unless `commit` is called."""

    users: UserRepository
    sessions: SessionRepository
    jobs: JobQueue
    runs: RunRepository

    def evidence_for(self, user_id: UUID) -> EvidenceRepository: ...
    def entries_for(self, user_id: UUID) -> EntryRepository: ...
    def preferences_for(self, user_id: UUID) -> PreferenceRepository: ...

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
