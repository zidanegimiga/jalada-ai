import uuid
from dataclasses import replace
from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DbSession
from sqlalchemy.orm import sessionmaker

from jalada.modules.accounts.domain.users import User
from jalada.modules.ledger.domain.money_accounts import (
    MoneyAccount,
    MoneyAccountKind,
    default_accounts,
)
from jalada.sql_unit_of_work import SqlUnitOfWork

pytestmark = pytest.mark.integration

NOW = datetime(2026, 11, 14, 9, 0, tzinfo=UTC)


def new_user(session_factory: sessionmaker[DbSession]) -> User:
    user = User(uuid.uuid4(), f"{uuid.uuid4().hex}@example.com", "Jane", NOW)
    with SqlUnitOfWork(session_factory) as work:
        work.users.add(user, None)
        work.commit()
    return user


def test_accounts_are_kept_per_user(session_factory: sessionmaker[DbSession]) -> None:
    user = new_user(session_factory)
    stranger = new_user(session_factory)
    bank = MoneyAccount(uuid.uuid4(), user.id, MoneyAccountKind.BANK, "KCB", False, NOW)
    with SqlUnitOfWork(session_factory) as work:
        for account in [*default_accounts(user.id, NOW), bank]:
            work.money_accounts_for(user.id).add(account)
        work.commit()

    with SqlUnitOfWork(session_factory) as work:
        names = [(a.name, a.tracked) for a in work.money_accounts_for(user.id).all()]
        assert sorted(names) == [("Cash", True), ("KCB", False), ("M-Pesa", True)]
        assert work.money_accounts_for(stranger.id).all() == []


def test_names_are_unique_per_user(session_factory: sessionmaker[DbSession]) -> None:
    user = new_user(session_factory)
    [mpesa, _] = default_accounts(user.id, NOW)
    with SqlUnitOfWork(session_factory) as work:
        work.money_accounts_for(user.id).add(mpesa)
        work.commit()

    with SqlUnitOfWork(session_factory) as work, pytest.raises(IntegrityError):
        work.money_accounts_for(user.id).add(replace(mpesa, id=uuid.uuid4()))


def test_an_account_cannot_be_added_for_someone_else(
    session_factory: sessionmaker[DbSession],
) -> None:
    user = new_user(session_factory)
    stranger = new_user(session_factory)
    [mpesa, _] = default_accounts(stranger.id, NOW)

    with SqlUnitOfWork(session_factory) as work, pytest.raises(PermissionError):
        work.money_accounts_for(user.id).add(mpesa)
