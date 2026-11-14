import uuid
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta

import pytest
from alembic import command
from database_fixtures import DATABASE_URL
from samples import confirmed_entry
from sqlalchemy.orm import Session as DbSession
from sqlalchemy.orm import sessionmaker
from test_ledger_storage import setup_evidence

from jalada.core.database.migrate import alembic_config
from jalada.modules.ledger.domain.audit import Actor, AuditAction, SubjectType, event
from jalada.modules.ledger.domain.entries import EntryStatus
from jalada.modules.ledger.domain.transactions import EvidenceRole, from_entry
from jalada.sql_unit_of_work import SqlUnitOfWork

pytestmark = pytest.mark.integration

NOW = datetime(2026, 11, 14, 9, 0, tzinfo=UTC)


def test_events_are_kept_per_user_oldest_first(session_factory: sessionmaker[DbSession]) -> None:
    user, evidence, _ = setup_evidence(session_factory)
    stranger, _, _ = setup_evidence(session_factory)
    entry = replace(
        confirmed_entry(user.id, date(2026, 11, 4), 15000, "out", "personal_food"),
        evidence_id=evidence.id,
    )
    proposed = from_entry(replace(entry, status=EntryStatus.PROPOSED), None, EvidenceRole.OTHER)
    confirmed = from_entry(entry, None, EvidenceRole.OTHER)
    later = event(
        user.id,
        SubjectType.TRANSACTION,
        entry.id,
        Actor.USER,
        AuditAction.CONFIRMED,
        proposed,
        confirmed,
        NOW + timedelta(minutes=5),
    )
    first = event(
        user.id,
        SubjectType.TRANSACTION,
        entry.id,
        Actor.PIPELINE,
        AuditAction.PROPOSED,
        None,
        proposed,
        NOW,
    )
    with SqlUnitOfWork(session_factory) as work:
        work.audit_for(user.id).add(later)
        work.audit_for(user.id).add(first)
        work.commit()

    with SqlUnitOfWork(session_factory) as work:
        assert work.audit_for(user.id).for_subject(entry.id) == [first, later]
        assert work.audit_for(user.id).all() == [first, later]
        assert work.audit_for(stranger.id).all() == []
        with pytest.raises(PermissionError):
            work.audit_for(stranger.id).add(first)


def test_old_revisions_are_copied_into_the_trail(session_factory: sessionmaker[DbSession]) -> None:
    user, evidence, _ = setup_evidence(session_factory)
    entry = replace(
        confirmed_entry(user.id, date(2026, 11, 4), 15000, "out", "personal_food"),
        evidence_id=evidence.id,
    )
    proposed = replace(entry, status=EntryStatus.PROPOSED)
    rejected = replace(entry, id=uuid.uuid4(), status=EntryStatus.REJECTED)
    with SqlUnitOfWork(session_factory) as work:
        for each in (entry, rejected):
            work.entries_for(user.id).add(each)
            work.transactions_for(user.id).add(from_entry(each, None, EvidenceRole.OTHER))
        work.entries_for(user.id).add_revision(proposed, entry, NOW)
        work.entries_for(user.id).add_revision(proposed, rejected, NOW)
        work.commit()

    assert DATABASE_URL
    command.downgrade(alembic_config(DATABASE_URL), "0011")
    command.upgrade(alembic_config(DATABASE_URL), "head")

    with SqlUnitOfWork(session_factory) as work:
        trail = work.audit_for(user.id)
        [kept] = trail.for_subject(entry.id)
        [refused] = trail.for_subject(rejected.id)
    assert (kept.subject_type, kept.actor, kept.action) == (
        SubjectType.TRANSACTION,
        Actor.USER,
        AuditAction.CONFIRMED,
    )
    assert kept.after is not None and kept.after["status"] == "confirmed"
    assert refused.action == AuditAction.REJECTED


def test_events_at_the_same_moment_keep_the_order_they_were_written(
    session_factory: sessionmaker[DbSession],
) -> None:
    user, evidence, _ = setup_evidence(session_factory)
    entry = replace(
        confirmed_entry(user.id, date(2026, 11, 4), 15000, "out", "personal_food"),
        evidence_id=evidence.id,
    )
    payment = from_entry(entry, None, EvidenceRole.OTHER)
    written = [
        event(user.id, SubjectType.TRANSACTION, entry.id, Actor.USER, action, None, payment, NOW)
        for action in (AuditAction.PROPOSED, AuditAction.CORRECTED, AuditAction.REJECTED)
    ]
    with SqlUnitOfWork(session_factory) as work:
        for each in written:
            work.audit_for(user.id).add(each)
        work.commit()

    with SqlUnitOfWork(session_factory) as work:
        assert work.audit_for(user.id).for_subject(entry.id) == written
