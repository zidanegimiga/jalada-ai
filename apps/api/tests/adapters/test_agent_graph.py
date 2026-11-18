import uuid
from datetime import date
from decimal import Decimal
from typing import Any

from fakes import ScriptedModel
from fakes.agent import TotalPaid, answer, use_tool
from langgraph.checkpoint.memory import InMemorySaver

from jalada.modules.agent.adapters.orchestration.graph import (
    FAILED,
    OUT_OF_BUDGET,
    WITHHELD,
    LangGraphRunner,
)
from jalada.modules.agent.application.ports import TurnRequest
from jalada.modules.agent.application.tools import ToolRegistry
from jalada.modules.agent.domain.progress import Progress, Stage
from jalada.modules.agent.domain.run import Budget, Outcome, StepKind
from jalada.modules.pipeline.domain.model import ModelFailed

ME, SOMEONE_ELSE = uuid.uuid4(), uuid.uuid4()
TOTALS = {ME: {"KPLC": "4500.00"}, SOMEONE_ELSE: {"KPLC": "99000.00"}}


def ask(
    *replies: dict[str, Any] | Exception,
    question: str = "How much did I pay KPLC?",
    budget: Budget | None = None,
    tool: TotalPaid | None = None,
    checkpointer: InMemorySaver | None = None,
) -> tuple[Any, ScriptedModel]:
    model = ScriptedModel(*replies)
    runner = LangGraphRunner(
        model, ToolRegistry([tool or TotalPaid(TOTALS)]), budget or Budget(), checkpointer
    )
    request = TurnRequest(uuid.uuid4(), ME, question, (), date(2026, 11, 18))
    return runner.run(request), model


def test_it_looks_up_then_answers_from_what_it_found() -> None:
    result, model = ask(
        use_tool("total_paid", counterparty="KPLC"), answer("You paid KPLC Ksh 4,500.")
    )

    assert (result.outcome, result.text) == (Outcome.ANSWERED, "You paid KPLC Ksh 4,500.")
    assert [(s.kind, s.outcome) for s in result.steps] == [
        (StepKind.MODEL, "tool"),
        (StepKind.TOOL, "ok"),
        (StepKind.MODEL, "answer"),
    ]
    assert '"total": "4500.00"' in model.calls[1]["content"]
    assert result.usage.cost_usd == Decimal("0.002")


def test_tools_only_ever_see_the_person_asking() -> None:
    tool = TotalPaid(TOTALS)

    ask(
        use_tool("total_paid", counterparty="KPLC", user_id=str(SOMEONE_ELSE)),
        answer("Done."),
        tool=tool,
    )

    assert tool.seen == [ME]


def test_the_person_asking_is_never_in_the_prompt() -> None:
    _, model = ask(use_tool("total_paid", counterparty="KPLC"), answer("Ksh 4,500."))

    assert all(str(ME) not in call["content"] for call in model.calls)


def test_an_unusable_reply_is_explained_and_tried_again() -> None:
    result, model = ask(use_tool("delete_everything"), answer("I can only look things up."))

    assert result.outcome == Outcome.ANSWERED
    assert "There is no tool called 'delete_everything'" in model.calls[1]["content"]
    assert result.steps[0].outcome == "unusable"


def test_an_amount_not_in_the_records_is_sent_back_once() -> None:
    result, model = ask(
        use_tool("total_paid", counterparty="KPLC"),
        answer("You paid Ksh 4,800."),
        answer("You paid Ksh 4,500."),
    )

    assert (result.outcome, result.text) == (Outcome.ANSWERED, "You paid Ksh 4,500.")
    assert "amounts no tool returned: 4800" in model.calls[2]["content"]


def test_an_answer_that_stays_ungrounded_is_withheld() -> None:
    result, _ = ask(
        use_tool("total_paid", counterparty="KPLC"),
        answer("You paid Ksh 4,800."),
        answer("Definitely Ksh 4,800."),
    )

    assert (result.outcome, result.text) == (Outcome.WITHHELD, WITHHELD)


def test_amounts_the_person_gave_can_be_repeated() -> None:
    result, _ = ask(
        answer("I cannot say if Ksh 2,000 is too much."), question="Is Ksh 2,000 too much?"
    )

    assert result.outcome == Outcome.ANSWERED


def test_it_stops_when_the_budget_runs_out() -> None:
    lookups = [use_tool("total_paid", counterparty="KPLC") for _ in range(3)]

    result, model = ask(*lookups, budget=Budget(max_steps=2))

    assert (result.outcome, result.text) == (Outcome.OUT_OF_BUDGET, OUT_OF_BUDGET)
    assert len(model.calls) == 2


def test_a_failed_model_ends_the_turn_politely() -> None:
    result, _ = ask(ModelFailed("every model failed"))

    assert (result.outcome, result.text) == (Outcome.FAILED, FAILED)
    assert result.steps[0].outcome == "failed"


def test_a_failed_lookup_is_reported_to_the_model_without_details() -> None:
    class Broken(TotalPaid):
        def run(self, context: Any, arguments: Any) -> dict[str, Any]:
            raise RuntimeError("connection to 10.0.0.5 refused for 0712345678")

    result, model = ask(
        use_tool("total_paid", counterparty="KPLC"),
        answer("I could not look that up."),
        tool=Broken({}),
    )

    assert result.outcome == Outcome.ANSWERED
    assert result.steps[1].outcome == "failed"
    assert "This lookup failed" in model.calls[1]["content"]
    assert "0712345678" not in model.calls[1]["content"]


def test_progress_is_reported_as_the_turn_goes() -> None:
    model = ScriptedModel(use_tool("total_paid", counterparty="KPLC"), answer("Ksh 4,500."))
    runner = LangGraphRunner(model, ToolRegistry([TotalPaid(TOTALS)]), Budget())
    seen: list[Progress] = []

    runner.run(TurnRequest(uuid.uuid4(), ME, "KPLC?", (), date(2026, 11, 18)), seen.append)

    assert seen == [
        Progress(Stage.THINKING),
        Progress(Stage.LOOKING_UP, "total_paid", "Looking it up"),
        Progress(Stage.THINKING),
        Progress(Stage.CHECKING),
    ]


def test_a_finished_turn_leaves_no_checkpoint() -> None:
    saver = InMemorySaver()

    ask(use_tool("total_paid", counterparty="KPLC"), answer("Ksh 4,500."), checkpointer=saver)

    assert list(saver.list(None)) == []
