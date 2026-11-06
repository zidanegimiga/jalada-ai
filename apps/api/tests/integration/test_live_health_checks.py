import os

import pytest
from sqlalchemy import Engine

from jalada.adapters.database.unit_of_work import create_database_engine
from jalada.adapters.health import DatabaseCheck, StorageCheck
from jalada.adapters.storage.s3_store import EncryptedS3EvidenceStore, create_s3_client

pytestmark = pytest.mark.integration


def test_the_database_check_passes_on_a_live_database(engine: Engine) -> None:
    assert DatabaseCheck(engine).ok()


def test_the_database_check_fails_when_nothing_answers() -> None:
    nowhere = create_database_engine("postgresql+psycopg://u:p@127.0.0.1:1/db?connect_timeout=1")

    assert not DatabaseCheck(nowhere).ok()


def test_the_storage_check_needs_the_bucket(s3_store: EncryptedS3EvidenceStore) -> None:
    client = create_s3_client(os.environ["JALADA_TEST_S3_ENDPOINT"], "us-east-1", "test", "test")

    assert StorageCheck(client, "jalada-test").ok()
    assert not StorageCheck(client, "no-such-bucket-here").ok()
