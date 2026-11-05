import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session as DbSession
from sqlalchemy.orm import sessionmaker

from jalada.adapters.database.unit_of_work import SqlUnitOfWork
from jalada.application.ports import PipelineRun
from jalada.domain.evidence import Evidence, EvidenceKind, EvidenceSource, EvidenceStatus
from jalada.domain.users import User
from jalada.pipeline.run_types import StepRecord

pytestmark = pytest.mark.integration

NOW = datetime(2026, 11, 5, 9, 0, tzinfo=UTC)


def test_everything_for_one_user_is_read_back(session_factory: sessionmaker[DbSession]) -> None:
    user = User(uuid.uuid4(), f"{uuid.uuid4().hex}@example.com", "Jane", NOW)
    evidence = Evidence(
        uuid.uuid4(),
        user.id,
        EvidenceSource.WEB_PASTE,
        EvidenceKind.UNKNOWN,
        EvidenceStatus.RECEIVED,
        "text/plain",
        10,
        "c" * 64,
        "key",
        NOW,
    )
    run = PipelineRun(
        uuid.uuid4(), user.id, evidence.id, "proposed", 1, 5, 6, Decimal("0.001"), NOW, NOW
    )
    steps = [
        StepRecord("detect", 1, {"text_length": 10}, {"kind": "mpesa_message"}, "ok", 1),
        StepRecord("extract", 1, {"method": "rules"}, {}, "nothing", 2),
    ]
    with SqlUnitOfWork(session_factory) as work:
        work.users.add(user, None)
        work.evidence_for(user.id).add(evidence)
        work.runs.add(run, steps)
        work.commit()

    with SqlUnitOfWork(session_factory) as work:
        assert work.evidence_for(user.id).all() == [evidence]
        [(saved, saved_steps)] = work.runs.for_user(user.id)
        assert work.runs.for_user(uuid.uuid4()) == []

    assert saved == run
    assert saved_steps == steps
