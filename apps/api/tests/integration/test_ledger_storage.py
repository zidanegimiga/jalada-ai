import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DbSession
from sqlalchemy.orm import sessionmaker

from jalada.adapters.database.unit_of_work import SqlUnitOfWork
from jalada.application.ports import PipelineRun
from jalada.domain.categories import Direction, Purpose
from jalada.domain.entries import Entry, EntryKind, EntryStatus
from jalada.domain.evidence import Evidence, EvidenceKind, EvidenceSource, EvidenceStatus
from jalada.domain.users import User
from jalada.pipeline.run_types import StepRecord

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


def test_entries_are_found_by_mpesa_code_only_for_their_owner(
    session_factory: sessionmaker[DbSession],
) -> None:
    user, evidence, run = setup_evidence(session_factory)
    stranger, _, _ = setup_evidence(session_factory)
    with SqlUnitOfWork(session_factory) as work:
        work.entries_for(user.id).add(make_entry(user, evidence, run, "UK5AB1CD23"))
        work.evidence_for(user.id).set_outcome(
            evidence.id, EvidenceKind.MPESA_MESSAGE, EvidenceStatus.PROPOSED
        )
        work.commit()

    with SqlUnitOfWork(session_factory) as work:
        assert work.entries_for(user.id).has_mpesa_code("UK5AB1CD23")
        assert not work.entries_for(stranger.id).has_mpesa_code("UK5AB1CD23")
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
