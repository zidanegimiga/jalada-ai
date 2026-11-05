from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from types import TracebackType
from typing import IO, TYPE_CHECKING, Any, Protocol, Self
from uuid import UUID

from jalada.domain.categories import Purpose

if TYPE_CHECKING:
    from jalada.application.account_export import AccountData
from jalada.domain.entries import Entry
from jalada.domain.evidence import Evidence, EvidenceKind, EvidenceStatus
from jalada.domain.ledger import LedgerFilter, LedgerPosition, Total
from jalada.domain.sessions import Session
from jalada.domain.tax_year import TaxYearReport
from jalada.domain.users import User
from jalada.pipeline.classifier import Preference
from jalada.pipeline.run_types import StepRecord


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
    def delete(self, user_id: UUID) -> None: ...


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
    def set_status(self, evidence_id: UUID, status: EvidenceStatus) -> None: ...
    def needing_entry(self, limit: int) -> list[Evidence]: ...
    def all(self) -> list[Evidence]: ...


@dataclass(frozen=True)
class Revision:
    entry_id: UUID
    before: dict[str, Any]
    after: dict[str, Any]
    changed_at: datetime


class EntryRepository(Protocol):
    """Ledger entries for one user."""

    def add(self, entry: Entry) -> None: ...
    def get(self, entry_id: UUID) -> Entry | None: ...
    def for_evidence(self, evidence_id: UUID) -> Entry | None: ...
    def update(self, entry: Entry) -> None: ...
    def add_revision(self, before: Entry, after: Entry, changed_at: datetime) -> None: ...
    def pending(self, limit: int) -> list[Entry]: ...
    def confirmed(
        self, filters: LedgerFilter, after: LedgerPosition | None, limit: int
    ) -> list[Entry]: ...
    def monthly_totals(self, year: int) -> list[Total]: ...
    def all(self) -> list[Entry]: ...
    def revisions(self) -> list[Revision]: ...
    def has_mpesa_code(self, code: str) -> bool: ...
    def has_certificate_serial(self, serial: str) -> bool: ...


class PreferenceRepository(Protocol):
    def all(self) -> dict[str, Preference]: ...
    def remember(self, counterparty_key: str, category: str, purpose: Purpose) -> None: ...


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
    def for_user(self, user_id: UUID) -> list[tuple[PipelineRun, list[StepRecord]]]: ...


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
    def discard_for(self, user_id: UUID) -> None: ...


class TelegramLinks(Protocol):
    """Links between Telegram accounts and users. Looked up by either side."""

    def save_code(self, user_id: UUID, code_hash: str, expires_at: datetime) -> None: ...
    def use_code(self, code_hash: str, now: datetime) -> UUID | None: ...
    def link(self, user_id: UUID, telegram_user_id: int, chat_id: int, at: datetime) -> None: ...
    def user_for(self, telegram_user_id: int) -> UUID | None: ...
    def chat_for(self, user_id: UUID) -> int | None: ...


class UnitOfWork(Protocol):
    """One database transaction. Nothing is saved unless `commit` is called."""

    users: UserRepository
    sessions: SessionRepository
    jobs: JobQueue
    runs: RunRepository
    telegram: TelegramLinks

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


class TextReader(Protocol):
    """Turns stored evidence into text. None when there is no text to read."""

    def read(self, content_type: str, data: bytes) -> str | None: ...


class WorkbookWriter(Protocol):
    """Turns a tax-year report into a spreadsheet file."""

    content_type: str

    def write(self, report: TaxYearReport) -> bytes: ...


class ChatChannel(Protocol):
    """A chat app the user can send evidence through, such as Telegram."""

    def send(self, chat_id: int, text: str) -> None: ...
    def download(self, file_id: str, max_bytes: int) -> bytes | None: ...


class Limiter(Protocol):
    """Counts attempts per key. False once any key is over its limit."""

    def allow(self, *keys: str) -> bool: ...


class ProcessingNotifier(Protocol):
    """Tells the user what the pipeline made of their evidence."""

    def notify(self, evidence: Evidence, outcome: str, entry: Entry | None) -> None: ...


class ArchiveWriter(Protocol):
    """Writes everything held about one user into a single downloadable file."""

    content_type: str
    extension: str

    def write(
        self, data: "AccountData", originals: Iterator[tuple[Evidence, bytes]], out: IO[bytes]
    ) -> None: ...


class Clock(Protocol):
    def now(self) -> datetime: ...
