import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session as DbSession
from sqlalchemy.orm import sessionmaker

from jalada.modules.accounts.domain.consent import ModelConsent
from jalada.modules.accounts.domain.users import User
from jalada.sql_unit_of_work import SqlUnitOfWork

pytestmark = pytest.mark.integration

NOW = datetime(2026, 11, 18, 9, 0, tzinfo=UTC)


def test_a_consent_is_kept_replaced_and_withdrawn(
    session_factory: sessionmaker[DbSession],
) -> None:
    user = User(uuid.uuid4(), f"{uuid.uuid4().hex}@example.com", "J", NOW)
    with SqlUnitOfWork(session_factory) as work:
        work.users.add(user, None)
        work.model_consents.give(ModelConsent(user.id, "Google, United States", NOW))
        work.commit()
    later = ModelConsent(user.id, "OpenAI, United States", NOW + timedelta(days=1))
    with SqlUnitOfWork(session_factory) as work:
        work.model_consents.give(later)
        work.commit()

    with SqlUnitOfWork(session_factory) as work:
        assert work.model_consents.get(user.id) == later
        work.model_consents.withdraw(user.id)
        work.commit()
    with SqlUnitOfWork(session_factory) as work:
        assert work.model_consents.get(user.id) is None
