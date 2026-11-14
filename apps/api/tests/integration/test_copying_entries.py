"""Migration 0011 copies entries written before transactions existed, and refuses to finish
if any entry and its transaction disagree."""

import uuid
from dataclasses import replace
from datetime import UTC, date, datetime

import pytest
from alembic import command
from database_fixtures import DATABASE_URL
from samples import certificate, confirmed_entry
from sqlalchemy import text
from sqlalchemy.orm import Session as DbSession
from sqlalchemy.orm import sessionmaker
from test_ledger_storage import setup_evidence

from jalada.core.database.migrate import alembic_config
from jalada.modules.evidence.domain.evidence import EvidenceKind, EvidenceStatus
from jalada.modules.ledger.domain.categories import Purpose
from jalada.modules.ledger.domain.entries import EntryStatus
from jalada.modules.ledger.domain.money_accounts import MoneyAccountKind, default_accounts
from jalada.modules.ledger.domain.transactions import (
    EvidenceRole,
    LinkedBy,
    TransactionLine,
    TransactionStatus,
    from_entry,
)
from jalada.sql_unit_of_work import SqlUnitOfWork

pytestmark = pytest.mark.integration

NOW = datetime(2026, 11, 14, 9, 0, tzinfo=UTC)


def run_copy() -> None:
    """Runs migration 0011 again over whatever the test has saved."""
    assert DATABASE_URL
    config = alembic_config(DATABASE_URL)
    command.downgrade(config, "0010")
    command.upgrade(config, "head")


def test_old_entries_are_copied_with_their_line_role_and_account(
    session_factory: sessionmaker[DbSession],
) -> None:
    user, message, run = setup_evidence(session_factory)
    accounts = default_accounts(user.id, NOW)
    paid = replace(
        confirmed_entry(user.id, date(2026, 10, 1), 15000, "out", "personal_food"),
        evidence_id=message.id,
        run_id=run.id,
        mpesa_code="UK5AB1CD23",
    )
    waiting = replace(
        paid,
        id=uuid.uuid4(),
        status=EntryStatus.PROPOSED,
        mpesa_code=None,
        run_id=None,
        category=None,
        purpose=Purpose.UNSURE,
        confirmed_at=None,
    )
    cert = replace(
        certificate(user.id, date(2026, 3, 3), 4_000_000, 200_000, "CLIENT"), evidence_id=message.id
    )
    with SqlUnitOfWork(session_factory) as work:
        for account in accounts:
            work.money_accounts_for(user.id).add(account)
        work.evidence_for(user.id).set_outcome(
            message.id, EvidenceKind.MPESA_MESSAGE, EvidenceStatus.CONFIRMED
        )
        for entry in (paid, waiting, cert):
            work.entries_for(user.id).add(entry)
        work.commit()

    run_copy()

    mpesa = next(a.id for a in accounts if a.kind == MoneyAccountKind.MPESA)
    with SqlUnitOfWork(session_factory) as work:
        transactions = work.transactions_for(user.id)
        copied = transactions.get(paid.id)
        assert copied == from_entry(paid, mpesa, EvidenceRole.PAYMENT_PROOF)
        assert copied.evidence[0].linked_by == LinkedBy.PIPELINE
        typed = transactions.get(waiting.id)
        assert typed is not None and typed.status == TransactionStatus.PROPOSED
        assert typed.lines == (TransactionLine(15000, None, Purpose.UNSURE),)
        assert typed.evidence[0].linked_by == LinkedBy.USER
        assert transactions.get(cert.id) is None, "certificates stay entries"


def test_a_transaction_that_disagrees_with_its_entry_stops_the_copy(
    session_factory: sessionmaker[DbSession],
) -> None:
    user, message, _ = setup_evidence(session_factory)
    entry = replace(
        confirmed_entry(user.id, date(2026, 10, 1), 15000, "out", "personal_food"),
        evidence_id=message.id,
    )
    wrong = from_entry(replace(entry, amount_cents=99900), None, EvidenceRole.OTHER)
    with SqlUnitOfWork(session_factory) as work:
        work.entries_for(user.id).add(entry)
        work.transactions_for(user.id).add(wrong)
        work.commit()

    try:
        with pytest.raises(RuntimeError, match="1 entries do not match"):
            run_copy()
    finally:
        with session_factory() as db:
            db.execute(text("DELETE FROM transactions WHERE id = :id"), {"id": wrong.id})
            db.commit()
        command.upgrade(alembic_config(DATABASE_URL or ""), "head")

    with SqlUnitOfWork(session_factory) as work:
        fixed = work.transactions_for(user.id).get(entry.id)
    assert fixed is not None and fixed.amount_cents == 15000
