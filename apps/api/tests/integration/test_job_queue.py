from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session as DbSession
from sqlalchemy.orm import sessionmaker

from jalada.sql_unit_of_work import SqlUnitOfWork

pytestmark = pytest.mark.integration


def enqueue(session_factory: sessionmaker[DbSession], count: int) -> None:
    with SqlUnitOfWork(session_factory) as work:
        for n in range(count):
            work.jobs.enqueue("work", {"n": str(n)})
        work.commit()


def test_two_workers_never_claim_the_same_job(session_factory: sessionmaker[DbSession]) -> None:
    enqueue(session_factory, 2)
    now = datetime.now(UTC) + timedelta(seconds=1)

    # Both transactions are open at once, like two workers polling at the same moment.
    with SqlUnitOfWork(session_factory) as first, SqlUnitOfWork(session_factory) as second:
        one = first.jobs.claim(now, 300)
        two = second.jobs.claim(now, 300)
        first.commit()
        second.commit()

    assert one is not None and two is not None
    assert one.id != two.id
    assert one.attempts == two.attempts == 1


def test_a_job_with_an_expired_lock_is_claimed_again(
    session_factory: sessionmaker[DbSession],
) -> None:
    enqueue(session_factory, 1)
    claim_time = datetime.now(UTC) + timedelta(seconds=1)
    with SqlUnitOfWork(session_factory) as work:
        claimed = work.jobs.claim(claim_time, 300)
        work.commit()

    with SqlUnitOfWork(session_factory) as work:
        assert work.jobs.claim(claim_time + timedelta(seconds=10), 300) is None
        again = work.jobs.claim(claim_time + timedelta(seconds=301), 300)

    assert claimed is not None and again is not None
    assert again.id == claimed.id and again.attempts == 2


def test_failed_jobs_wait_until_their_retry_time(session_factory: sessionmaker[DbSession]) -> None:
    enqueue(session_factory, 1)
    now = datetime.now(UTC) + timedelta(seconds=1)
    with SqlUnitOfWork(session_factory) as work:
        job = work.jobs.claim(now, 300)
        assert job is not None
        work.jobs.fail(job.id, "ConnectionError", now + timedelta(minutes=2))
        work.commit()

    with SqlUnitOfWork(session_factory) as work:
        assert work.jobs.claim(now + timedelta(minutes=1), 300) is None
        assert work.jobs.claim(now + timedelta(minutes=3), 300) is not None
