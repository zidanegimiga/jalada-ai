import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session as DbSession
from sqlalchemy.orm import sessionmaker

from jalada.adapters.database.unit_of_work import SqlUnitOfWork
from jalada.adapters.storage.s3_store import EncryptedS3EvidenceStore
from jalada.domain.evidence import Evidence, EvidenceKind, EvidenceSource, EvidenceStatus
from jalada.domain.users import User

pytestmark = pytest.mark.integration

NOW = datetime(2026, 11, 5, 9, 0, tzinfo=UTC)


def add_user(session_factory: sessionmaker[DbSession], email: str) -> User:
    user = User(uuid.uuid4(), email, "Someone", NOW)
    with SqlUnitOfWork(session_factory) as work:
        work.users.add(user, None)
        work.commit()
    return user


def make_evidence(user: User, sha256: str = "a" * 64) -> Evidence:
    return Evidence(
        uuid.uuid4(),
        user.id,
        EvidenceSource.WEB_UPLOAD,
        EvidenceKind.UNKNOWN,
        EvidenceStatus.RECEIVED,
        "image/jpeg",
        10,
        sha256,
        "key",
        NOW,
    )


def test_evidence_and_its_job_are_saved_together(session_factory: sessionmaker[DbSession]) -> None:
    user = add_user(session_factory, "jane@example.com")
    evidence = make_evidence(user)
    with SqlUnitOfWork(session_factory) as work:
        work.evidence_for(user.id).add(evidence)
        work.jobs.enqueue("process_evidence", {"evidence_id": str(evidence.id)})
        work.commit()

    with SqlUnitOfWork(session_factory) as work:
        assert work.evidence_for(user.id).get(evidence.id) == evidence
        assert work.evidence_for(user.id).get_by_fingerprint("a" * 64) == evidence
    with session_factory() as db:
        job = db.execute(text("SELECT kind, payload, status FROM jobs")).one()
    assert job == ("process_evidence", {"evidence_id": str(evidence.id)}, "queued")


def test_another_users_repository_cannot_see_the_evidence(
    session_factory: sessionmaker[DbSession],
) -> None:
    owner = add_user(session_factory, "owner@example.com")
    stranger = add_user(session_factory, "stranger@example.com")
    evidence = make_evidence(owner)
    with SqlUnitOfWork(session_factory) as work:
        work.evidence_for(owner.id).add(evidence)
        work.commit()

    with SqlUnitOfWork(session_factory) as work:
        theirs = work.evidence_for(stranger.id)
        assert theirs.get(evidence.id) is None
        assert theirs.get_by_fingerprint("a" * 64) is None
        assert theirs.list_recent(10) == []
        with pytest.raises(PermissionError):
            theirs.add(make_evidence(owner, "b" * 64))


def test_s3_store_keeps_only_ciphertext(s3_store: EncryptedS3EvidenceStore) -> None:
    evidence_id, user_id = uuid.uuid4(), uuid.uuid4()

    s3_store.put(evidence_id, user_id, b"receipt bytes")

    raw = s3_store._client.get_object(Bucket="jalada-test", Key=f"evidence/{user_id}/{evidence_id}")
    assert b"receipt bytes" not in raw["Body"].read()
    assert s3_store.get(evidence_id, user_id, s3_store.key_id) == b"receipt bytes"
    s3_store.delete(evidence_id, user_id)
