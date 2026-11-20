import os
import uuid
from datetime import date

import pytest
from fakes import ScriptedModel
from fakes.agent import TotalPaid, answer, use_tool
from sqlalchemy import Engine, text

from jalada.modules.agent.adapters.orchestration.checkpoints import postgres_checkpoints
from jalada.modules.agent.adapters.orchestration.graph import LangGraphRunner
from jalada.modules.agent.application.ports import TurnRequest
from jalada.modules.agent.application.tools import ToolRegistry
from jalada.modules.agent.domain.run import Budget, Outcome

pytestmark = pytest.mark.integration

SCHEMA = "assistant_turns_test"


def test_turns_run_on_postgres_and_leave_nothing_behind(engine: Engine) -> None:
    saver = postgres_checkpoints(os.environ["JALADA_TEST_DATABASE_URL"], SCHEMA)
    postgres_checkpoints(os.environ["JALADA_TEST_DATABASE_URL"], SCHEMA)  # safe to run again
    user = uuid.uuid4()
    model = ScriptedModel(use_tool("total_paid", counterparty="KPLC"), answer("Ksh 4,500."))
    runner = LangGraphRunner(
        model, ToolRegistry([TotalPaid({user: {"KPLC": "4500"}})]), Budget(), saver
    )

    result = runner.run(TurnRequest(uuid.uuid4(), user, "KPLC?", (), date(2026, 11, 18)))

    assert result.outcome == Outcome.ANSWERED
    # The schema keeps this test apart from the tables production keeps beside the app's own.
    with engine.connect() as connection:
        left = connection.scalar(text(f"SELECT count(*) FROM {SCHEMA}.checkpoints"))  # noqa: S608
    assert left == 0
