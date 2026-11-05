"""Fixtures for integration tests against a real Postgres database."""

import os
from collections.abc import Iterator

import pytest
from alembic import command
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session, sessionmaker

from jalada.adapters.database.migrate import alembic_config
from jalada.adapters.database.unit_of_work import create_database_engine

DATABASE_URL = os.environ.get("JALADA_TEST_DATABASE_URL")


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    if not DATABASE_URL:
        pytest.skip("JALADA_TEST_DATABASE_URL is not set")
    command.upgrade(alembic_config(DATABASE_URL), "head")
    engine = create_database_engine(DATABASE_URL)
    yield engine
    engine.dispose()


@pytest.fixture
def session_factory(engine: Engine) -> Iterator[sessionmaker[Session]]:
    yield sessionmaker(engine)
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE users, sessions CASCADE"))
