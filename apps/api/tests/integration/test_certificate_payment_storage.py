import uuid
from dataclasses import replace
from datetime import UTC, date, datetime

import pytest
from samples import certificate, confirmed_entry, deposit
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DbSession
from sqlalchemy.orm import sessionmaker
from test_ledger_storage import setup_evidence

from jalada.adapters.database.unit_of_work import SqlUnitOfWork
from jalada.domain.categories import Direction, Purpose
from jalada.domain.entries import Entry
from jalada.domain.ledger import Total

pytestmark = pytest.mark.integration

NOW = datetime(2026, 11, 5, 9, 0, tzinfo=UTC)


def save(session_factory: sessionmaker[DbSession], *entries: Entry) -> uuid.UUID:
    """Saves the entries for a new user, against one piece of evidence. Returns the user id."""
    user, evidence, _ = setup_evidence(session_factory)
    with SqlUnitOfWork(session_factory) as work:
        for entry in entries:
            work.entries_for(user.id).add(
                replace(entry, user_id=user.id, evidence_id=evidence.id, run_id=None)
            )
        work.commit()
    return user.id


def test_links_are_kept_per_user_and_a_payment_settles_one_certificate(
    session_factory: sessionmaker[DbSession],
) -> None:
    anyone = uuid.uuid4()
    first = certificate(anyone, date(2026, 3, 3), 4_000_000, 200_000, "CLIENT")
    second = certificate(anyone, date(2026, 3, 4), 4_000_000, 200_000, "CLIENT")
    paid = deposit(anyone, date(2026, 3, 5), 3_800_000, "CLIENT")
    user = save(session_factory, first, second, paid)
    other = save(session_factory)

    with SqlUnitOfWork(session_factory) as work:
        work.certificate_payments_for(user).link(first.id, paid.id, NOW)
        work.commit()
    with SqlUnitOfWork(session_factory) as work:
        assert work.certificate_payments_for(user).links() == {paid.id: first.id}
        assert work.certificate_payments_for(other).links() == {}
        work.certificate_payments_for(other).unlink(first.id, paid.id)
        work.commit()
    with SqlUnitOfWork(session_factory) as work, pytest.raises(IntegrityError):
        work.certificate_payments_for(user).link(second.id, paid.id, NOW)

    with SqlUnitOfWork(session_factory) as work:
        assert work.certificate_payments_for(user).links() == {paid.id: first.id}
        work.certificate_payments_for(user).unlink(first.id, paid.id)
        work.commit()
    with SqlUnitOfWork(session_factory) as work:
        assert work.certificate_payments_for(user).links() == {}


def test_incoming_money_and_monthly_totals_count_linked_payments_once(
    session_factory: sessionmaker[DbSession],
) -> None:
    anyone = uuid.uuid4()
    cert = certificate(anyone, date(2026, 3, 3), 4_000_000, 200_000, "CLIENT")
    paid = deposit(anyone, date(2026, 3, 5), 3_800_000, "CLIENT")
    spent = confirmed_entry(anyone, date(2026, 3, 6), 50_000, "out", "business_stock")
    user = save(session_factory, cert, paid, spent)

    with SqlUnitOfWork(session_factory) as work:
        incoming = work.entries_for(user).incoming(date(2026, 3, 1), date(2026, 3, 31))
        assert [e.id for e in incoming] == [paid.id]
        work.certificate_payments_for(user).link(cert.id, paid.id, NOW)
        work.commit()

    with SqlUnitOfWork(session_factory) as work:
        assert sorted(work.entries_for(user).monthly_totals(2026), key=str) == sorted(
            [
                Total(3, Direction.IN, Purpose.BUSINESS, 4_000_000),
                Total(3, Direction.OUT, Purpose.BUSINESS, 50_000),
            ],
            key=str,
        )


def test_deleting_the_user_deletes_their_links(session_factory: sessionmaker[DbSession]) -> None:
    anyone = uuid.uuid4()
    cert = certificate(anyone, date(2026, 3, 3), 4_000_000, 200_000, "CLIENT")
    paid = deposit(anyone, date(2026, 3, 5), 3_800_000, "CLIENT")
    user = save(session_factory, cert, paid)
    with SqlUnitOfWork(session_factory) as work:
        work.certificate_payments_for(user).link(cert.id, paid.id, NOW)
        work.commit()

    with session_factory() as db, db.begin():
        db.execute(text("DELETE FROM users WHERE id = :id"), {"id": user})
        left = db.scalar(
            text("SELECT count(*) FROM certificate_payments WHERE user_id = :id"), {"id": user}
        )

    assert left == 0
