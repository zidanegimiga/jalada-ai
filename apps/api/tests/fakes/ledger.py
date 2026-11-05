"""Fake repositories for entries, preferences and pipeline runs."""

from datetime import datetime
from uuid import UUID

from jalada.application.ports import (
    PipelineRun,
)
from jalada.domain.categories import Direction, Purpose
from jalada.domain.entries import Entry, EntryStatus
from jalada.domain.ledger import LedgerFilter, LedgerPosition, Total
from jalada.pipeline.classifier import Preference
from jalada.pipeline.run_types import StepRecord


class FakeEntries:
    def __init__(
        self, rows: dict[UUID, Entry], user_id: UUID, revisions: list[tuple[Entry, Entry]]
    ) -> None:
        self.rows = rows
        self._user_id = user_id
        self._revisions = revisions

    def add(self, entry: Entry) -> None:
        assert entry.user_id == self._user_id
        self.rows[entry.id] = entry

    def get(self, entry_id: UUID) -> Entry | None:
        return next((e for e in self._mine() if e.id == entry_id), None)

    def for_evidence(self, evidence_id: UUID) -> Entry | None:
        return next((e for e in self._mine() if e.evidence_id == evidence_id), None)

    def update(self, entry: Entry) -> None:
        assert entry.user_id == self._user_id and entry.id in self.rows
        self.rows[entry.id] = entry

    def add_revision(self, before: Entry, after: Entry, changed_at: datetime) -> None:
        self._revisions.append((before, after))

    def pending(self, limit: int) -> list[Entry]:
        waiting = (EntryStatus.PROPOSED, EntryStatus.NEEDS_REVIEW)
        return [e for e in self._mine() if e.status in waiting][:limit]

    def confirmed(
        self, filters: LedgerFilter, after: LedgerPosition | None, limit: int
    ) -> list[Entry]:
        found = [
            e for e in self._mine() if e.status == EntryStatus.CONFIRMED and _keeps(filters, e)
        ]
        found.sort(key=lambda e: (e.occurred_on, e.id), reverse=True)
        if after:
            found = [
                e for e in found if (e.occurred_on, e.id) < (after.occurred_on, after.entry_id)
            ]
        return found[:limit]

    def monthly_totals(self, year: int) -> list[Total]:
        sums: dict[tuple[int, Direction, Purpose], int] = {}
        for e in self._mine():
            if e.status == EntryStatus.CONFIRMED and e.occurred_on and e.occurred_on.year == year:
                key = (e.occurred_on.month, e.direction or Direction.OUT, e.purpose)
                sums[key] = sums.get(key, 0) + (e.amount_cents or 0)
        return [Total(m, d, p, cents) for (m, d, p), cents in sums.items()]

    def has_mpesa_code(self, code: str) -> bool:
        return any(e.mpesa_code == code for e in self._mine())

    def has_certificate_serial(self, serial: str) -> bool:
        return any(e.certificate_serial == serial for e in self._mine())

    def _mine(self) -> list[Entry]:
        return [e for e in self.rows.values() if e.user_id == self._user_id]


def _keeps(filters: LedgerFilter, entry: Entry) -> bool:
    day = entry.occurred_on
    return not (
        (filters.start and (day is None or day < filters.start))
        or (filters.end and (day is None or day > filters.end))
        or (filters.direction and entry.direction != filters.direction)
        or (filters.purpose and entry.purpose != filters.purpose)
        or (filters.category and entry.category != filters.category)
    )


class FakePreferences:
    def __init__(self, preferences: dict[str, Preference]) -> None:
        self._preferences = preferences

    def all(self) -> dict[str, Preference]:
        return dict(self._preferences)

    def remember(self, counterparty_key: str, category: str, purpose: Purpose) -> None:
        old = self._preferences.get(counterparty_key)
        same = old is not None and (old.category, old.purpose) == (category, purpose)
        times = old.times_used + 1 if old and same else 1
        self._preferences[counterparty_key] = Preference(category, purpose, times)


class FakeRuns:
    def __init__(self, rows: list[tuple[PipelineRun, list[StepRecord]]]) -> None:
        self.rows = rows

    def add(self, run: PipelineRun, steps: list[StepRecord]) -> None:
        self.rows.append((run, steps))
