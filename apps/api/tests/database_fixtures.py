"""Fixtures for integration tests against a real Postgres database."""

import contextlib
import os
from collections.abc import Iterator

import pytest
from alembic import command
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session, sessionmaker

from jalada.adapters.database.migrate import alembic_config
from jalada.adapters.database.unit_of_work import create_database_engine
from jalada.adapters.security.evidence_cipher import EvidenceCipher
from jalada.adapters.storage.s3_store import EncryptedS3EvidenceStore, create_s3_client

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
        # CASCADE also clears every table that refers to users.
        connection.execute(text("TRUNCATE users, jobs CASCADE"))


@pytest.fixture
def s3_store() -> EncryptedS3EvidenceStore:
    endpoint = os.environ.get("JALADA_TEST_S3_ENDPOINT")
    if not endpoint:
        pytest.skip("JALADA_TEST_S3_ENDPOINT is not set")
    client = create_s3_client(endpoint, "us-east-1", "test", "test")
    with contextlib.suppress(client.exceptions.BucketAlreadyOwnedByYou):
        client.create_bucket(Bucket="jalada-test")
    return EncryptedS3EvidenceStore(client, "jalada-test", [EvidenceCipher(b"t" * 32)])
