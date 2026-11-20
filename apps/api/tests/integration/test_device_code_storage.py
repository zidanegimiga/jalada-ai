import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session as DbSession
from sqlalchemy.orm import sessionmaker

from jalada.modules.accounts.domain.device_codes import DeviceCode
from jalada.modules.accounts.domain.users import User
from jalada.sql_unit_of_work import SqlUnitOfWork

pytestmark = pytest.mark.integration

NOW = datetime(2026, 11, 20, 9, 0, tzinfo=UTC)
CHALLENGE = "a" * 43


def saved_code(factory: sessionmaker[DbSession], expires_at: datetime) -> tuple[User, str]:
    user = User(uuid.uuid4(), f"{uuid.uuid4().hex}@example.com", "J", NOW)
    code_hash = uuid.uuid4().hex + uuid.uuid4().hex
    with SqlUnitOfWork(factory) as work:
        work.users.add(user, None)
        work.device_codes.add(DeviceCode(code_hash, user.id, CHALLENGE, expires_at))
        work.commit()
    return user, code_hash


def test_a_code_is_taken_once(session_factory: sessionmaker[DbSession]) -> None:
    user, code_hash = saved_code(session_factory, NOW + timedelta(minutes=2))

    with SqlUnitOfWork(session_factory) as work:
        taken = work.device_codes.take(code_hash, NOW)
        work.commit()
    with SqlUnitOfWork(session_factory) as work:
        again = work.device_codes.take(code_hash, NOW)

    assert taken == DeviceCode(code_hash, user.id, CHALLENGE, NOW + timedelta(minutes=2))
    assert again is None


def test_an_expired_code_is_removed_and_not_given_back(
    session_factory: sessionmaker[DbSession],
) -> None:
    _, code_hash = saved_code(session_factory, NOW - timedelta(seconds=1))

    with SqlUnitOfWork(session_factory) as work:
        assert work.device_codes.take(code_hash, NOW) is None
        work.commit()
    with SqlUnitOfWork(session_factory) as work:
        assert work.device_codes.take(code_hash, NOW - timedelta(days=1)) is None


def test_codes_go_with_the_account(session_factory: sessionmaker[DbSession]) -> None:
    user, code_hash = saved_code(session_factory, NOW + timedelta(minutes=2))

    with SqlUnitOfWork(session_factory) as work:
        work.users.delete(user.id)
        work.commit()
    with SqlUnitOfWork(session_factory) as work:
        assert work.device_codes.take(code_hash, NOW) is None
