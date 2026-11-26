from dataclasses import replace

import pytest
from sqlalchemy import select, text
from sqlalchemy.orm import Session as DbSession
from sqlalchemy.orm import sessionmaker
from test_transaction_storage import saved

from jalada.core.database.changes import settled_before
from jalada.modules.ledger.adapters.tables import TransactionRow
from jalada.modules.ledger.application.entry_changes import EntryChanges
from jalada.modules.ledger.domain.changes import START
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


def feed(session_factory: sessionmaker[DbSession]) -> EntryChanges:
    return EntryChanges(lambda: SqlUnitOfWork(session_factory))


def test_the_feed_gives_each_save_once_in_order(
    session_factory: sessionmaker[DbSession],
) -> None:
    transaction = saved(session_factory)
    changes = feed(session_factory)

    first = changes.since(transaction.user_id, START)
    with SqlUnitOfWork(session_factory) as work:
        work.transactions_for(transaction.user_id).update(
            replace(transaction, counterparty="SAMPLE SHOP")
        )
        work.commit()
    second = changes.since(transaction.user_id, first.next_position)

    assert [c.id for c in first.changes] == [transaction.id]
    assert [(c.id, c.version) for c in second.changes] == [(transaction.id, 2)]
    assert changes.since(transaction.user_id, second.next_position).changes == []


def test_a_save_still_running_comes_on_a_later_read_not_never(
    session_factory: sessionmaker[DbSession],
) -> None:
    transaction = saved(session_factory)
    changes = feed(session_factory)
    caught_up = changes.since(transaction.user_id, START).next_position

    with SqlUnitOfWork(session_factory) as slow:
        slow.transactions_for(transaction.user_id).update(
            replace(transaction, counterparty="SLOW SAVE")
        )
        # Another device reads while the save has not finished.
        during = changes.since(transaction.user_id, caught_up)
        slow.commit()
    after = changes.since(transaction.user_id, during.next_position)

    assert during.changes == []
    assert [c.entry.counterparty for c in after.changes if c.entry] == ["SLOW SAVE"]
