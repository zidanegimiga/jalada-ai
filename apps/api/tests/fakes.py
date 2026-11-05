"""In-memory stand-ins for the ports, for fast tests without a database."""

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import TracebackType
from typing import Any, Self
from uuid import UUID

from jalada.application.errors import GoogleSignInFailed
from jalada.application.ports import (
    EntryRepository,
    EvidenceRepository,
    GoogleProfile,
    Job,
    JobQueue,
    PipelineRun,
    PreferenceRepository,
    RunRepository,
    SessionRepository,
    UserCredentials,
    UserRepository,
)
from jalada.domain.entries import Entry
from jalada.domain.evidence import Evidence, EvidenceKind, EvidenceStatus
from jalada.domain.sessions import Session
from jalada.domain.users import User
from jalada.pipeline.classifier import Preference
from jalada.pipeline.model import ImageInput, ModelReply, ModelUsage
from jalada.pipeline.run_types import StepRecord


@dataclass
class Store:
    users: dict[UUID, UserCredentials] = field(default_factory=dict)
    google_subjects: dict[str, UUID] = field(default_factory=dict)
    evidence: dict[UUID, Evidence] = field(default_factory=dict)
    jobs: list[tuple[str, dict[str, str]]] = field(default_factory=list)
    entries: dict[UUID, Entry] = field(default_factory=dict)
    preferences: dict[UUID, dict[str, Preference]] = field(default_factory=dict)
    runs: list[tuple[PipelineRun, list[StepRecord]]] = field(default_factory=list)
    # Jobs for the job runner: id to [job, status, run_after].
    queue: dict[int, list[Any]] = field(default_factory=dict)
    sessions: dict[str, Session] = field(default_factory=dict)


class FakeUsers:
    def __init__(
        self, users: dict[UUID, UserCredentials], google_subjects: dict[str, UUID]
    ) -> None:
        self.rows = users
        self.google_subjects = google_subjects

    def add(self, user: User, password_hash: str | None, google_subject: str | None = None) -> None:
        self.rows[user.id] = UserCredentials(user, password_hash)
        if google_subject:
            self.google_subjects[google_subject] = user.id

    def get(self, user_id: UUID) -> User | None:
        found = self.rows.get(user_id)
        return found.user if found else None

    def get_credentials(self, email: str) -> UserCredentials | None:
        return next((c for c in self.rows.values() if c.user.email == email), None)

    def get_by_google_subject(self, subject: str) -> User | None:
        user_id = self.google_subjects.get(subject)
        return self.get(user_id) if user_id else None

    def link_google(self, user_id: UUID, subject: str) -> None:
        self.google_subjects[subject] = user_id


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


class FakeEvidence:
    def __init__(self, rows: dict[UUID, Evidence], user_id: UUID) -> None:
        self.rows = rows
        self._user_id = user_id

    def add(self, evidence: Evidence) -> None:
        assert evidence.user_id == self._user_id
        self.rows[evidence.id] = evidence

    def get(self, evidence_id: UUID) -> Evidence | None:
        found = self.rows.get(evidence_id)
        return found if found and found.user_id == self._user_id else None

    def get_by_fingerprint(self, sha256: str) -> Evidence | None:
        return next((e for e in self._mine() if e.sha256 == sha256), None)

    def list_recent(self, limit: int) -> list[Evidence]:
        return sorted(self._mine(), key=lambda e: e.received_at, reverse=True)[:limit]

    def set_outcome(self, evidence_id: UUID, kind: EvidenceKind, status: EvidenceStatus) -> None:
        if evidence_id in self.rows and self.rows[evidence_id].user_id == self._user_id:
            self.rows[evidence_id] = replace(self.rows[evidence_id], kind=kind, status=status)

    def _mine(self) -> list[Evidence]:
        return [e for e in self.rows.values() if e.user_id == self._user_id]


class FakeJobs:
    def __init__(self, jobs: list[tuple[str, dict[str, str]]], queue: dict[int, list[Any]]) -> None:
        self.rows = jobs
        self.queue = queue

    def enqueue(self, kind: str, payload: dict[str, str]) -> None:
        self.rows.append((kind, payload))

    def claim(self, now: datetime, lock_seconds: int) -> Job | None:
        for job_id, (job, status, run_after) in sorted(self.queue.items()):
            if status == "queued" and run_after <= now:
                claimed: Job = replace(job, attempts=job.attempts + 1)
                self.queue[job_id] = [claimed, "running", run_after]
                return claimed
        return None

    def complete(self, job_id: int) -> None:
        self.queue[job_id][1] = "done"

    def fail(self, job_id: int, error: str, retry_at: datetime | None) -> None:
        job = self.queue[job_id][0]
        self.queue[job_id] = [job, "queued" if retry_at else "failed", retry_at]


class FakeEntries:
    def __init__(self, rows: dict[UUID, Entry], user_id: UUID) -> None:
        self.rows = rows
        self._user_id = user_id

    def add(self, entry: Entry) -> None:
        assert entry.user_id == self._user_id
        self.rows[entry.id] = entry

    def has_mpesa_code(self, code: str) -> bool:
        return any(e.mpesa_code == code for e in self._mine())

    def has_certificate_serial(self, serial: str) -> bool:
        return any(e.certificate_serial == serial for e in self._mine())

    def _mine(self) -> list[Entry]:
        return [e for e in self.rows.values() if e.user_id == self._user_id]


class FakePreferences:
    def __init__(self, preferences: dict[str, Preference]) -> None:
        self._preferences = preferences

    def all(self) -> dict[str, Preference]:
        return dict(self._preferences)


class FakeRuns:
    def __init__(self, rows: list[tuple[PipelineRun, list[StepRecord]]]) -> None:
        self.rows = rows

    def add(self, run: PipelineRun, steps: list[StepRecord]) -> None:
        self.rows.append((run, steps))


class FakeUnitOfWork:
    """Works on copies of the store and writes them back only on commit, like a transaction."""

    def __init__(self, store: Store) -> None:
        self._store = store

    def __enter__(self) -> Self:
        self._users = FakeUsers(dict(self._store.users), dict(self._store.google_subjects))
        self._sessions = FakeSessions(dict(self._store.sessions))
        self.users: UserRepository = self._users
        self.sessions: SessionRepository = self._sessions
        self._evidence = dict(self._store.evidence)
        self._jobs = FakeJobs(
            list(self._store.jobs), {k: list(v) for k, v in self._store.queue.items()}
        )
        self.jobs: JobQueue = self._jobs
        self._entries = dict(self._store.entries)
        self._runs = FakeRuns(list(self._store.runs))
        self.runs: RunRepository = self._runs
        return self

    def evidence_for(self, user_id: UUID) -> EvidenceRepository:
        return FakeEvidence(self._evidence, user_id)

    def entries_for(self, user_id: UUID) -> EntryRepository:
        return FakeEntries(self._entries, user_id)

    def preferences_for(self, user_id: UUID) -> PreferenceRepository:
        return FakePreferences(self._store.preferences.get(user_id, {}))

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        pass

    def commit(self) -> None:
        self._store.users = self._users.rows
        self._store.google_subjects = self._users.google_subjects
        self._store.evidence = self._evidence
        self._store.jobs = self._jobs.rows
        self._store.queue = self._jobs.queue
        self._store.entries = self._entries
        self._store.runs = self._runs.rows
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


class FakeGoogle:
    """Returns a preset profile for the code "good-code" and fails for anything else."""

    def __init__(self) -> None:
        self.profile = GoogleProfile("google-123", "jane@example.com", True, "Jane Doe")
        self.exchanged: list[tuple[str, str, str]] = []

    def authorization_url(self, state: str, nonce: str, code_verifier: str) -> str:
        return f"https://accounts.example.com/auth?state={state}"

    def exchange(self, code: str, nonce: str, code_verifier: str) -> GoogleProfile:
        self.exchanged.append((code, nonce, code_verifier))
        if code != "good-code":
            raise GoogleSignInFailed
        return self.profile


class FakeEvidenceStore:
    """Keeps evidence in memory, keyed by user and id."""

    key_id = "test-key"

    def __init__(self) -> None:
        self.objects: dict[tuple[UUID, UUID], bytes] = {}

    def put(self, evidence_id: UUID, user_id: UUID, data: bytes) -> None:
        self.objects[(user_id, evidence_id)] = data

    def get(self, evidence_id: UUID, user_id: UUID, key_id: str) -> bytes:
        return self.objects[(user_id, evidence_id)]

    def delete(self, evidence_id: UUID, user_id: UUID) -> None:
        self.objects.pop((user_id, evidence_id), None)


class FakeTextReader:
    """Plain text is decoded. Anything else reads as the text given for it, or nothing."""

    def __init__(self, pdf_text: str | None = None) -> None:
        self.pdf_text = pdf_text

    def read(self, content_type: str, data: bytes) -> str | None:
        if content_type.startswith("text/"):
            return data.decode()
        return self.pdf_text if content_type == "application/pdf" else None


def later(clock: FixedClock, minutes: int) -> datetime:
    return clock.now() + timedelta(minutes=minutes)


class ScriptedModel:
    """Answers with prepared replies, in order, and remembers what it was asked."""

    name = "scripted"

    def __init__(self, *replies: dict[str, Any] | Exception, tokens: int = 100) -> None:
        self._replies = list(replies)
        self._tokens = tokens
        self.calls: list[dict[str, Any]] = []

    def complete(
        self,
        instructions: str,
        content: str,
        schema: dict[str, Any],
        image: ImageInput | None = None,
    ) -> ModelReply:
        self.calls.append({"content": content, "schema": schema, "image": image})
        reply = self._replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        usage = ModelUsage(self._tokens, self._tokens // 2, Decimal("0.001"))
        return ModelReply(reply, usage)
