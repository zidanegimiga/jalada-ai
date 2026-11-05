"""Fake repositories for evidence and the job queue."""

from dataclasses import replace
from datetime import datetime
from typing import Any
from uuid import UUID

from jalada.application.ports import (
    Job,
)
from jalada.domain.entries import Entry
from jalada.domain.evidence import Evidence, EvidenceKind, EvidenceStatus


class FakeEvidence:
    def __init__(
        self, rows: dict[UUID, Evidence], user_id: UUID, entries: dict[UUID, Entry] | None = None
    ) -> None:
        self.rows = rows
        self._user_id = user_id
        self.entries = entries or {}

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

    def set_status(self, evidence_id: UUID, status: EvidenceStatus) -> None:
        if evidence_id in self.rows and self.rows[evidence_id].user_id == self._user_id:
            self.rows[evidence_id] = replace(self.rows[evidence_id], status=status)

    def needing_entry(self, limit: int) -> list[Evidence]:
        unread = (EvidenceStatus.NEEDS_REVIEW, EvidenceStatus.FAILED)
        with_entry = {entry.evidence_id for entry in self.entries.values()}
        found = [e for e in self._mine() if e.status in unread and e.id not in with_entry]
        return sorted(found, key=lambda e: e.received_at)[:limit]

    def all(self) -> list[Evidence]:
        return sorted(self._mine(), key=lambda e: e.received_at)

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
