import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session as DbSession
from sqlalchemy.orm import sessionmaker

from jalada.modules.accounts.domain.users import User
from jalada.sql_unit_of_work import SqlUnitOfWork

pytestmark = pytest.mark.integration

NOW = datetime(2026, 11, 5, 9, 0, tzinfo=UTC)


def add_user(session_factory: sessionmaker[DbSession]) -> uuid.UUID:
    user = User(uuid.uuid4(), f"{uuid.uuid4().hex}@example.com", "J", NOW)
    with SqlUnitOfWork(session_factory) as work:
        work.users.add(user, None)
        work.commit()
    return user.id


def test_codes_link_once_and_links_move(session_factory: sessionmaker[DbSession]) -> None:
    first, second = add_user(session_factory), add_user(session_factory)
    with SqlUnitOfWork(session_factory) as work:
        work.telegram.save_code(first, "a" * 64, NOW + timedelta(minutes=10))
        work.commit()

    with SqlUnitOfWork(session_factory) as work:
        assert work.telegram.use_code("a" * 64, NOW) == first
        work.telegram.link(first, 111, 222, NOW)
        work.commit()
    with SqlUnitOfWork(session_factory) as work:
        assert work.telegram.use_code("a" * 64, NOW) is None
        assert work.telegram.user_for(111) == first
        assert work.telegram.chat_for(first) == 222
        work.telegram.link(second, 111, 333, NOW)
        work.commit()

    with SqlUnitOfWork(session_factory) as work:
        assert work.telegram.user_for(111) == second
        assert work.telegram.chat_for(first) is None


def test_unlink_removes_the_link_and_waiting_codes(
    session_factory: sessionmaker[DbSession],
) -> None:
    user = add_user(session_factory)
    with SqlUnitOfWork(session_factory) as work:
        work.telegram.link(user, 444, 555, NOW)
        work.telegram.save_code(user, "c" * 64, NOW + timedelta(minutes=10))
        work.commit()

    with SqlUnitOfWork(session_factory) as work:
        work.telegram.unlink(user)
        work.commit()

    with SqlUnitOfWork(session_factory) as work:
        assert work.telegram.chat_for(user) is None
        assert work.telegram.use_code("c" * 64, NOW) is None


def test_expired_codes_do_not_work(session_factory: sessionmaker[DbSession]) -> None:
    user = add_user(session_factory)
    with SqlUnitOfWork(session_factory) as work:
        work.telegram.save_code(user, "b" * 64, NOW)
        work.commit()

    with SqlUnitOfWork(session_factory) as work:
        assert work.telegram.use_code("b" * 64, NOW + timedelta(seconds=1)) is None
