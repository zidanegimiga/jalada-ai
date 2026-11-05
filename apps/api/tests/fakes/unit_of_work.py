"""A fake transaction over the in-memory store."""

from types import TracebackType
from typing import Self
from uuid import UUID

from fakes.accounts import FakeSessions, FakeTelegramLinks, FakeUsers
from fakes.evidence import FakeEvidence, FakeJobs
from fakes.ledger import FakeEntries, FakePreferences, FakeRuns
from fakes.store import Store
from jalada.application.ports import (
    EntryRepository,
    EvidenceRepository,
    JobQueue,
    PreferenceRepository,
    RunRepository,
    SessionRepository,
    TelegramLinks,
    UserRepository,
)


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
        self._revisions = list(self._store.revisions)
        self._preferences = {user: dict(p) for user, p in self._store.preferences.items()}
        self._runs = FakeRuns(list(self._store.runs))
        self.runs: RunRepository = self._runs
        self._telegram = FakeTelegramLinks(
            dict(self._store.telegram_codes), dict(self._store.telegram_links)
        )
        self.telegram: TelegramLinks = self._telegram
        return self

    def evidence_for(self, user_id: UUID) -> EvidenceRepository:
        return FakeEvidence(self._evidence, user_id, self._entries)

    def entries_for(self, user_id: UUID) -> EntryRepository:
        return FakeEntries(self._entries, user_id, self._revisions)

    def preferences_for(self, user_id: UUID) -> PreferenceRepository:
        return FakePreferences(self._preferences.setdefault(user_id, {}))

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
        self._store.revisions = self._revisions
        self._store.telegram_codes = self._telegram.codes
        self._store.telegram_links = self._telegram.links
        self._store.preferences = self._preferences
        self._store.runs = self._runs.rows
        self._store.sessions = self._sessions.rows
        for user_id in self._users.deleted:
            self._cascade(user_id)

    def _cascade(self, user_id: UUID) -> None:
        """What the database's ON DELETE CASCADE does when a user row is deleted."""
        store = self._store
        store.sessions = {k: s for k, s in store.sessions.items() if s.user_id != user_id}
        store.evidence = {k: e for k, e in store.evidence.items() if e.user_id != user_id}
        store.entries = {k: e for k, e in store.entries.items() if e.user_id != user_id}
        store.revisions = [(b, a) for b, a in store.revisions if a.user_id != user_id]
        store.runs = [(r, s) for r, s in store.runs if r.user_id != user_id]
        store.preferences.pop(user_id, None)
        store.telegram_links.pop(user_id, None)
        store.telegram_codes = {k: c for k, c in store.telegram_codes.items() if c[0] != user_id}
        store.google_subjects = {k: u for k, u in store.google_subjects.items() if u != user_id}
