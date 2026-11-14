import uuid
from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from botocore.exceptions import ClientError
from samples import confirmed_entry
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session as DbSession
from sqlalchemy.orm import sessionmaker

from jalada.core.database.base import Base
from jalada.modules.accounts.application.account_deletion import AccountDeletion
from jalada.modules.accounts.domain.sessions import Session
from jalada.modules.accounts.domain.users import User
from jalada.modules.evidence.adapters.storage import EncryptedS3EvidenceStore
from jalada.modules.evidence.domain.evidence import (
    Evidence,
    EvidenceKind,
    EvidenceSource,
    EvidenceStatus,
)
from jalada.modules.ledger.domain.audit import Actor, AuditAction, SubjectType, event
from jalada.modules.ledger.domain.categories import Purpose
from jalada.modules.ledger.domain.money_accounts import default_accounts
from jalada.modules.ledger.domain.transactions import EvidenceRole, from_entry
from jalada.modules.pipeline.application.ports import PipelineRun
from jalada.modules.pipeline.domain.run_types import StepRecord
from jalada.sql_unit_of_work import SqlUnitOfWork

pytestmark = pytest.mark.integration

NOW = datetime(2026, 11, 5, 9, 0, tzinfo=UTC)


def test_everything_for_one_user_is_read_back(session_factory: sessionmaker[DbSession]) -> None:
    user = User(uuid.uuid4(), f"{uuid.uuid4().hex}@example.com", "Jane", NOW)
    evidence = Evidence(
        uuid.uuid4(),
        user.id,
        EvidenceSource.WEB_PASTE,
        EvidenceKind.UNKNOWN,
        EvidenceStatus.RECEIVED,
        "text/plain",
        10,
        "c" * 64,
        "key",
        NOW,
    )
    run = PipelineRun(
        uuid.uuid4(), user.id, evidence.id, "proposed", 1, 5, 6, Decimal("0.001"), NOW, NOW
    )
    steps = [
        StepRecord("detect", 1, {"text_length": 10}, {"kind": "mpesa_message"}, "ok", 1),
        StepRecord("extract", 1, {"method": "rules"}, {}, "nothing", 2),
    ]
    with SqlUnitOfWork(session_factory) as work:
        work.users.add(user, None)
        work.evidence_for(user.id).add(evidence)
        work.runs.add(run, steps)
        work.commit()

    with SqlUnitOfWork(session_factory) as work:
        assert work.evidence_for(user.id).all() == [evidence]
        [(saved, saved_steps)] = work.runs.for_user(user.id)
        assert work.runs.for_user(uuid.uuid4()) == []

    assert saved == run
    assert saved_steps == steps


def test_deleting_a_user_empties_every_table_and_the_bucket(
    session_factory: sessionmaker[DbSession], s3_store: EncryptedS3EvidenceStore
) -> None:
    user = User(uuid.uuid4(), f"{uuid.uuid4().hex}@example.com", "Jane", NOW)
    keep = User(uuid.uuid4(), f"{uuid.uuid4().hex}@example.com", "Keep", NOW)
    evidence = Evidence(
        uuid.uuid4(),
        user.id,
        EvidenceSource.WEB_PASTE,
        EvidenceKind.UNKNOWN,
        EvidenceStatus.RECEIVED,
        "text/plain",
        10,
        "d" * 64,
        s3_store.key_id,
        NOW,
    )
    run = PipelineRun(uuid.uuid4(), user.id, evidence.id, "proposed", 1, 0, 0, Decimal(0), NOW, NOW)
    entry = replace(
        confirmed_entry(user.id, date(2026, 11, 4), 15_000, "out", "personal_food"),
        evidence_id=evidence.id,
        run_id=run.id,
    )
    s3_store.put(evidence.id, user.id, b"receipt")
    with SqlUnitOfWork(session_factory) as work:
        work.users.add(user, "hash")
        work.users.add(keep, "hash")
        work.sessions.add(Session("e" * 64, user.id, NOW))
        work.evidence_for(user.id).add(evidence)
        work.runs.add(run, [StepRecord("detect", 1, {}, {}, "ok", 1)])
        work.entries_for(user.id).add(entry)
        work.entries_for(user.id).add_revision(entry, entry, NOW)
        work.preferences_for(user.id).remember("jane wanjiku", "personal_food", Purpose.PERSONAL)
        accounts = default_accounts(user.id, NOW)
        for account in accounts:
            work.money_accounts_for(user.id).add(account)
        work.transactions_for(user.id).add(
            from_entry(entry, accounts[0].id, EvidenceRole.PAYMENT_PROOF)
        )
        work.audit_for(user.id).add(
            event(
                user.id,
                SubjectType.TRANSACTION,
                entry.id,
                Actor.USER,
                AuditAction.CONFIRMED,
                None,
                entry,
                NOW,
            )
        )
        work.telegram.save_code(user.id, "f" * 64, NOW)
        work.telegram.link(user.id, 777, 888, NOW)
        work.jobs.enqueue(
            "process_evidence", {"evidence_id": str(evidence.id), "user_id": str(user.id)}
        )
        work.jobs.enqueue("process_evidence", {"evidence_id": "x", "user_id": str(keep.id)})
        work.commit()

    AccountDeletion(lambda: SqlUnitOfWork(session_factory), s3_store).delete(user.id, user.email)

    tables = [
        "users",
        "sessions",
        "evidence",
        "pipeline_runs",
        "entries",
        "counterparty_preferences",
        "money_accounts",
        "transactions",
        "transaction_lines",
        "transaction_evidence",
        "audit_events",
        "telegram_links",
        "telegram_link_codes",
    ]
    with session_factory() as db:
        for table in tables:
            rows = Base.metadata.tables[table]
            owner = rows.c.id if table == "users" else rows.c.user_id
            left = db.scalar(select(func.count()).select_from(rows).where(owner == user.id))
            assert left == 0, f"{table} still has rows"
        assert db.scalar(text("SELECT count(*) FROM pipeline_steps")) == 0
        assert db.scalar(text("SELECT count(*) FROM entry_revisions")) == 0
        assert db.scalar(text("SELECT count(*) FROM jobs")) == 1, (
            "only the other user's job is left"
        )
        assert db.scalar(text("SELECT count(*) FROM users WHERE id = :u"), {"u": keep.id}) == 1
    with pytest.raises(ClientError):
        s3_store.get(evidence.id, user.id, s3_store.key_id)
