import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session as DbSession
from sqlalchemy.orm import sessionmaker

from jalada.adapters.database.unit_of_work import SqlUnitOfWork
from jalada.application.errors import EmailAlreadyRegistered
from jalada.domain.sessions import Session
from jalada.domain.users import User

pytestmark = pytest.mark.integration

NOW = datetime(2026, 11, 5, 9, 0, tzinfo=UTC)


def make_user(email: str = "jane@example.com") -> User:
    return User(uuid.uuid4(), email, "Jane", NOW)


def test_users_and_sessions_round_trip(session_factory: sessionmaker[DbSession]) -> None:
    user = make_user()
    with SqlUnitOfWork(session_factory) as work:
        work.users.add(user, "hash")
        work.sessions.add(Session("a" * 64, user.id, NOW + timedelta(days=1)))
        work.commit()

    with SqlUnitOfWork(session_factory) as work:
        assert work.users.get(user.id) == user
        credentials = work.users.get_credentials("jane@example.com")
        assert credentials is not None and credentials.password_hash == "hash"
        assert work.sessions.get_active("a" * 64, NOW) is not None
        assert work.sessions.get_active("a" * 64, NOW + timedelta(days=2)) is None


def test_nothing_is_saved_without_commit(session_factory: sessionmaker[DbSession]) -> None:
    user = make_user()
    with SqlUnitOfWork(session_factory) as work:
        work.users.add(user, "hash")

    with SqlUnitOfWork(session_factory) as work:
        assert work.users.get(user.id) is None


def test_the_database_refuses_a_second_account_with_one_email(
    session_factory: sessionmaker[DbSession],
) -> None:
    with SqlUnitOfWork(session_factory) as work:
        work.users.add(make_user(), "hash")
        work.commit()

    with SqlUnitOfWork(session_factory) as work, pytest.raises(EmailAlreadyRegistered):
        work.users.add(make_user(), "hash")


def test_deleting_a_user_deletes_their_sessions(
    session_factory: sessionmaker[DbSession],
) -> None:
    user = make_user()
    with SqlUnitOfWork(session_factory) as work:
        work.users.add(user, "hash")
        work.sessions.add(Session("b" * 64, user.id, NOW + timedelta(days=1)))
        work.commit()

    with session_factory() as db, db.begin():
        db.execute(text("DELETE FROM users WHERE id = :id"), {"id": user.id})

    with SqlUnitOfWork(session_factory) as work:
        assert work.sessions.get_active("b" * 64, NOW) is None
