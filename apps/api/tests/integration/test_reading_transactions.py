"""Every screen that moves from entries to transactions shows the same records and the same
totals as before. Each test saves entries with their transactions, as the pipeline and
migration 0011 do, and compares the new reading with the old one."""

import uuid
from dataclasses import replace
from datetime import UTC, date, datetime

import pytest
from samples import certificate, confirmed_entry, deposit
from sqlalchemy.orm import Session as DbSession
from sqlalchemy.orm import sessionmaker
from test_ledger_storage import setup_evidence

from jalada.modules.accounts.domain.users import User
from jalada.modules.ledger.application.ledger import Ledger
from jalada.modules.ledger.domain.categories import Direction, Purpose
from jalada.modules.ledger.domain.entries import Entry, EntryKind, EntryStatus
from jalada.modules.ledger.domain.ledger import LedgerFilter, LedgerPosition
from jalada.modules.ledger.domain.transactions import EvidenceRole, from_entry
from jalada.sql_unit_of_work import SqlUnitOfWork

pytestmark = pytest.mark.integration

NOW = datetime(2026, 11, 14, 9, 0, tzinfo=UTC)
FILTERS = [
    LedgerFilter(),
    LedgerFilter(start=date(2026, 1, 1), end=date(2026, 1, 31)),
    LedgerFilter(direction=Direction.IN),
    LedgerFilter(purpose=Purpose.BUSINESS),
    LedgerFilter(category="personal_food"),
]


def save(session_factory: sessionmaker[DbSession]) -> tuple[User, list[Entry]]:
    user, evidence, _ = setup_evidence(session_factory)
    entries = [
        confirmed_entry(user.id, date(2026, 1, 5), 4_000_000, "in", "consultancy_fees"),
        confirmed_entry(user.id, date(2026, 1, 5), 500_000, "in", "family_support"),
        confirmed_entry(user.id, date(2026, 1, 20), 25_000, "out", "business_airtime_data"),
        confirmed_entry(user.id, date(2026, 2, 3), 80_000, "out", "personal_food"),
        confirmed_entry(user.id, date(2025, 12, 30), 99_000, "out", "personal_food"),
        certificate(user.id, date(2026, 3, 3), 4_000_000, 200_000, "CLIENT"),
        deposit(user.id, date(2026, 3, 5), 3_800_000, "CLIENT"),
        replace(
            confirmed_entry(user.id, date(2026, 1, 6), 1_000, "out", "personal_food"),
            status=EntryStatus.PROPOSED,
        ),
    ]
    entries = [replace(e, evidence_id=evidence.id) for e in entries]
    with SqlUnitOfWork(session_factory) as work:
        for entry in entries:
            work.entries_for(user.id).add(entry)
            if entry.kind == EntryKind.TRANSACTION:
                work.transactions_for(user.id).add(from_entry(entry, None, EvidenceRole.OTHER))
        work.certificate_payments_for(user.id).link(entries[5].id, entries[6].id, NOW)
        work.commit()
    return user, entries


def every_page(ledger: Ledger, user_id: uuid.UUID, filters: LedgerFilter) -> list[Entry]:
    seen: list[Entry] = []
    after: LedgerPosition | None = None
    while True:
        page = ledger.page(user_id, filters, after, size=2)
        seen += page.entries
        if page.next_position is None:
            return seen
        after = page.next_position


def test_the_ledger_lists_the_same_records_page_by_page(
    session_factory: sessionmaker[DbSession],
) -> None:
    user, _ = save(session_factory)
    ledger = Ledger(lambda: SqlUnitOfWork(session_factory))

    for filters in FILTERS:
        with SqlUnitOfWork(session_factory) as work:
            before = work.entries_for(user.id).confirmed(filters, None, 100)
        assert every_page(ledger, user.id, filters) == before, filters
