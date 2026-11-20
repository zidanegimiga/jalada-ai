from dataclasses import replace

import pytest
from sqlalchemy import select, text
from sqlalchemy.orm import Session as DbSession
from sqlalchemy.orm import sessionmaker
from test_transaction_storage import saved

from jalada.core.database.changes import settled_before
from jalada.modules.ledger.adapters.tables import TransactionRow
from jalada.sql_unit_of_work import SqlUnitOfWork

pytestmark = pytest.mark.integration


def changed_in(session_factory: sessionmaker[DbSession], transaction_id: object) -> int:
    with session_factory() as db:
        return (
            db.scalar(select(TransactionRow.changed_in).where(TransactionRow.id == transaction_id))
            or 0
        )


def test_each_save_moves_the_version_on_whatever_the_caller_held(
    session_factory: sessionmaker[DbSession],
) -> None:
    transaction = saved(session_factory)

    for _ in range(2):
        with SqlUnitOfWork(session_factory) as work:
            work.transactions_for(transaction.user_id).update(
                replace(transaction, counterparty="SAMPLE SHOP")
            )
            work.commit()

    with SqlUnitOfWork(session_factory) as work:
        found = work.transactions_for(transaction.user_id).get(transaction.id)
    assert found is not None and found.version == 3


def test_a_save_is_marked_with_its_own_database_transaction(
    session_factory: sessionmaker[DbSession],
) -> None:
    transaction = saved(session_factory)
    before = changed_in(session_factory, transaction.id)

    with SqlUnitOfWork(session_factory) as work:
        work.transactions_for(transaction.user_id).update(transaction)
        work.commit()

    after = changed_in(session_factory, transaction.id)
    assert after > before
    # Finished, so a reader now may read it.
    with session_factory() as db:
        assert settled_before(db) > after


def test_a_save_still_running_is_left_for_a_later_read(
    session_factory: sessionmaker[DbSession],
) -> None:
    transaction = saved(session_factory)

    with SqlUnitOfWork(session_factory) as work:
        work.transactions_for(transaction.user_id).update(transaction)
        running = changed_in_open(work)
        with session_factory() as reader:
            assert settled_before(reader) <= running
        work.commit()


def changed_in_open(work: SqlUnitOfWork) -> int:
    """The id of the unit of work's own, still open, database transaction."""
    return int(work._db.execute(text("SELECT pg_current_xact_id()::text::bigint")).scalar_one())
