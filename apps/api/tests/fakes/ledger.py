"""Fake repositories for entries, preferences and pipeline runs."""

from collections.abc import Collection
from dataclasses import asdict
from datetime import date, datetime
from uuid import UUID

from jalada.modules.ledger.application.ports import Revision
from jalada.modules.ledger.domain.categories import Direction, Purpose
from jalada.modules.ledger.domain.entries import Entry, EntryKind, EntryStatus
from jalada.modules.ledger.domain.ledger import LedgerFilter, LedgerPosition, Total
from jalada.modules.ledger.domain.money_accounts import MoneyAccount
from jalada.modules.pipeline.application.ports import PipelineRun
from jalada.modules.pipeline.domain.classifier import Preference
from jalada.modules.pipeline.domain.run_types import StepRecord


class FakeEntries:
    def __init__(
        self,
        rows: dict[UUID, Entry],
        user_id: UUID,
        revisions: list[tuple[Entry, Entry]],
        linked_payments: Collection[UUID] = (),
    ) -> None:
        self.rows = rows
        self._user_id = user_id
        self._revisions = revisions
        self._linked_payments = linked_payments

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
            if e.id in self._linked_payments:
                continue
            if e.status == EntryStatus.CONFIRMED and e.occurred_on and e.occurred_on.year == year:
                key = (e.occurred_on.month, e.direction or Direction.OUT, e.purpose)
                sums[key] = sums.get(key, 0) + (e.amount_cents or 0)
        return [Total(m, d, p, cents) for (m, d, p), cents in sums.items()]

    def has_mpesa_code(self, code: str) -> bool:
        return any(e.mpesa_code == code for e in self._mine())

    def has_certificate_serial(self, serial: str) -> bool:
        return any(e.certificate_serial == serial for e in self._mine())

    def all(self) -> list[Entry]:
        return sorted(self._mine(), key=lambda e: e.created_at)

    def incoming(self, start: date, end: date) -> list[Entry]:
        found = [
            e
            for e in self._mine()
            if e.status == EntryStatus.CONFIRMED
            and e.kind == EntryKind.TRANSACTION
            and e.direction == Direction.IN
            and e.occurred_on
            and start <= e.occurred_on <= end
        ]
        return sorted(found, key=lambda e: e.occurred_on or start)

    def revisions(self) -> list[Revision]:
        mine = {e.id for e in self._mine()}
        return [
            Revision(after.id, asdict(before), asdict(after), datetime.min)
            for before, after in self._revisions
            if after.id in mine
        ]

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


class FakeCertificatePayments:
    def __init__(self, rows: dict[UUID, tuple[UUID, UUID]], user_id: UUID) -> None:
        # Payment id to (user id, certificate id).
        self.rows = rows
        self._user_id = user_id

    def links(self) -> dict[UUID, UUID]:
        return {p: c for p, (u, c) in self.rows.items() if u == self._user_id}

    def link(self, certificate_id: UUID, payment_id: UUID, at: datetime) -> None:
        assert payment_id not in self.rows, "the database refuses a second link"
        self.rows[payment_id] = (self._user_id, certificate_id)

    def unlink(self, certificate_id: UUID, payment_id: UUID) -> None:
        if self.rows.get(payment_id) == (self._user_id, certificate_id):
            del self.rows[payment_id]


class FakeMoneyAccounts:
    def __init__(self, rows: dict[UUID, MoneyAccount], user_id: UUID) -> None:
        self.rows = rows
        self._user_id = user_id

    def all(self) -> list[MoneyAccount]:
        mine = [a for a in self.rows.values() if a.user_id == self._user_id]
        return sorted(mine, key=lambda a: (a.created_at, a.name))

    def add(self, account: MoneyAccount) -> None:
        if account.user_id != self._user_id:
            raise PermissionError("Account belongs to another user")
        assert account.name not in {a.name for a in self.all()}, "the database refuses it"
        self.rows[account.id] = account


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

    def for_user(self, user_id: UUID) -> list[tuple[PipelineRun, list[StepRecord]]]:
        return [(run, steps) for run, steps in self.rows if run.user_id == user_id]
