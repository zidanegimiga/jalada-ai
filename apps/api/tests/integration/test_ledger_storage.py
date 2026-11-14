import uuid
from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from samples import confirmed_entry
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DbSession
from sqlalchemy.orm import sessionmaker

from jalada.modules.accounts.domain.users import User
from jalada.modules.evidence.domain.evidence import (
    Evidence,
    EvidenceKind,
    EvidenceSource,
    EvidenceStatus,
)
from jalada.modules.ledger.domain.categories import Direction, Purpose
from jalada.modules.ledger.domain.entries import Entry, EntryKind, EntryStatus
from jalada.modules.ledger.domain.ledger import LedgerFilter, LedgerPosition, Total
from jalada.modules.pipeline.application.ports import PipelineRun
from jalada.modules.pipeline.domain.run_types import StepRecord
from jalada.sql_unit_of_work import SqlUnitOfWork

pytestmark = pytest.mark.integration

NOW = datetime(2026, 11, 5, 9, 0, tzinfo=UTC)


def setup_evidence(session_factory: sessionmaker[DbSession]) -> tuple[User, Evidence, PipelineRun]:
    user = User(uuid.uuid4(), f"{uuid.uuid4().hex}@example.com", "Jane", NOW)
    evidence = Evidence(
        uuid.uuid4(),
        user.id,
        EvidenceSource.WEB_PASTE,
        EvidenceKind.UNKNOWN,
        EvidenceStatus.RECEIVED,
        "text/plain",
        10,
        uuid.uuid4().hex * 2,
        "key",
        NOW,
    )
    run = PipelineRun(uuid.uuid4(), user.id, evidence.id, "proposed", 1, 0, 0, Decimal(0), NOW, NOW)
    step = StepRecord("detect", 1, {"text_length": 10}, {"kind": "mpesa_message"}, "ok", 3)
    with SqlUnitOfWork(session_factory) as work:
        work.users.add(user, None)
        work.evidence_for(user.id).add(evidence)
        work.runs.add(run, [step])
        work.commit()
    return user, evidence, run


def make_entry(user: User, evidence: Evidence, run: PipelineRun, code: str) -> Entry:
    return Entry(
        uuid.uuid4(),
        user.id,
        evidence.id,
        run.id,
        EntryKind.TRANSACTION,
        EntryStatus.PROPOSED,
        date(2026, 11, 5),
        Direction.OUT,
        15000,
        "JANE WANJIKU",
        None,
        code,
        None,
        None,
        Purpose.PERSONAL,
        "personal_food",
        0.95,
        NOW,
    )


def test_an_entry_saves_beside_its_evidence_outcome(
    session_factory: sessionmaker[DbSession],
) -> None:
    user, evidence, run = setup_evidence(session_factory)
    with SqlUnitOfWork(session_factory) as work:
        work.entries_for(user.id).add(make_entry(user, evidence, run, "UK5AB1CD23"))
        work.evidence_for(user.id).set_outcome(
            evidence.id, EvidenceKind.MPESA_MESSAGE, EvidenceStatus.PROPOSED
        )
        work.commit()

    with SqlUnitOfWork(session_factory) as work:
        saved = work.evidence_for(user.id).get(evidence.id)
        assert saved is not None and saved.status == EvidenceStatus.PROPOSED


def test_the_database_refuses_a_second_entry_with_the_same_code(
    session_factory: sessionmaker[DbSession],
) -> None:
    user, evidence, run = setup_evidence(session_factory)
    with SqlUnitOfWork(session_factory) as work:
        work.entries_for(user.id).add(make_entry(user, evidence, run, "UK5AB1CD23"))
        work.commit()

    with SqlUnitOfWork(session_factory) as work, pytest.raises(IntegrityError):
        work.entries_for(user.id).add(make_entry(user, evidence, run, "UK5AB1CD23"))


def test_runs_keep_their_steps(session_factory: sessionmaker[DbSession]) -> None:
    _, _, run = setup_evidence(session_factory)

    with session_factory() as db:
        steps = db.execute(
            text("SELECT step, output, duration_ms FROM pipeline_steps WHERE run_id = :id"),
            {"id": run.id},
        ).all()

    assert steps == [("detect", {"kind": "mpesa_message"}, 3)]


def test_preferences_are_read_per_user(session_factory: sessionmaker[DbSession]) -> None:
    user, _, _ = setup_evidence(session_factory)
    with session_factory() as db, db.begin():
        db.execute(
            text(
                "INSERT INTO counterparty_preferences "
                "(user_id, counterparty_key, category, purpose, times_used) "
                "VALUES (:user, 'jane wanjiku', 'personal_food', 'personal', 2)"
            ),
            {"user": user.id},
        )

    with SqlUnitOfWork(session_factory) as work:
        preference = work.preferences_for(user.id).all()["jane wanjiku"]

    assert (preference.category, preference.purpose, preference.times_used) == (
        "personal_food",
        Purpose.PERSONAL,
        2,
    )


def test_confirming_updates_the_entry_and_keeps_the_revision(
    session_factory: sessionmaker[DbSession],
) -> None:
    user, evidence, run = setup_evidence(session_factory)
    entry = make_entry(user, evidence, run, "UK5AB1CD99")
    with SqlUnitOfWork(session_factory) as work:
        work.entries_for(user.id).add(entry)
        work.commit()
    confirmed = replace(entry, status=EntryStatus.CONFIRMED, amount_cents=16000, confirmed_at=NOW)

    with SqlUnitOfWork(session_factory) as work:
        assert work.entries_for(user.id).pending(10) == [entry]
        work.entries_for(user.id).update(confirmed)
        work.entries_for(user.id).add_revision(entry, confirmed, NOW)
        work.commit()

    with SqlUnitOfWork(session_factory) as work:
        assert work.entries_for(user.id).get(entry.id) == confirmed
        assert work.entries_for(user.id).pending(10) == []
        assert work.entries_for(user.id).for_evidence(evidence.id) == confirmed
    with session_factory() as db:
        before, after = db.execute(text("SELECT before, after FROM entry_revisions")).one()
    assert (before["amount_cents"], after["amount_cents"]) == ("15000", "16000")


def test_remembered_choices_count_up_and_reset_on_change(
    session_factory: sessionmaker[DbSession],
) -> None:
    user, _, _ = setup_evidence(session_factory)

    for category in ["personal_food", "personal_food", "personal_food", "personal_other"]:
        with SqlUnitOfWork(session_factory) as work:
            work.preferences_for(user.id).remember("jane wanjiku", category, Purpose.PERSONAL)
            work.commit()
        with SqlUnitOfWork(session_factory) as work:
            last = work.preferences_for(user.id).all()["jane wanjiku"]

    assert (last.category, last.times_used) == ("personal_other", 1)


def test_unread_evidence_without_an_entry_waits_for_one(
    session_factory: sessionmaker[DbSession],
) -> None:
    user, evidence, run = setup_evidence(session_factory)
    with SqlUnitOfWork(session_factory) as work:
        work.evidence_for(user.id).set_status(evidence.id, EvidenceStatus.NEEDS_REVIEW)
        work.commit()

    with SqlUnitOfWork(session_factory) as work:
        assert [e.id for e in work.evidence_for(user.id).needing_entry(10)] == [evidence.id]
        work.entries_for(user.id).add(make_entry(user, evidence, run, "UK5AB1CD98"))
        work.commit()

    with SqlUnitOfWork(session_factory) as work:
        assert work.evidence_for(user.id).needing_entry(10) == []


def test_ledger_queries_filter_page_and_total_in_postgres(
    session_factory: sessionmaker[DbSession],
) -> None:
    user, evidence, _ = setup_evidence(session_factory)
    rows = [
        (date(2026, 1, 5), 4_000_000, "in", "consultancy_fees"),
        (date(2026, 1, 20), 25_000, "out", "business_airtime_data"),
        (date(2026, 1, 20), 5_000, "out", "business_airtime_data"),
        (date(2026, 2, 3), 80_000, "out", "personal_food"),
    ]
    with SqlUnitOfWork(session_factory) as work:
        for day, cents, direction, category in rows:
            entry = replace(
                confirmed_entry(user.id, day, cents, direction, category), evidence_id=evidence.id
            )
            work.entries_for(user.id).add(entry)
        work.commit()

    with SqlUnitOfWork(session_factory) as work:
        entries = work.entries_for(user.id)
        first = entries.confirmed(LedgerFilter(), None, 2)
        last = first[-1]
        assert last.occurred_on is not None
        rest = entries.confirmed(LedgerFilter(), LedgerPosition(last.occurred_on, last.id), 10)
        business = entries.confirmed(LedgerFilter(purpose=Purpose.BUSINESS), None, 10)
        totals = entries.monthly_totals(2026)

    assert len(first) + len(rest) == 4
    assert {e.id for e in first}.isdisjoint({e.id for e in rest})
    assert len(business) == 3
    assert Total(1, Direction.OUT, Purpose.BUSINESS, 30_000) in totals
    assert Total(1, Direction.IN, Purpose.BUSINESS, 4_000_000) in totals
    assert Total(2, Direction.OUT, Purpose.PERSONAL, 80_000) in totals


def test_the_payers_tax_number_is_kept(session_factory: sessionmaker[DbSession]) -> None:
    user, evidence, run = setup_evidence(session_factory)
    entry = replace(make_entry(user, evidence, run, "UK5AB1CD97"), payer_tax_number="P000000000A")
    with SqlUnitOfWork(session_factory) as work:
        work.entries_for(user.id).add(entry)
        work.commit()

    with SqlUnitOfWork(session_factory) as work:
        saved = work.entries_for(user.id).get(entry.id)

    assert saved is not None and saved.payer_tax_number == "P000000000A"
