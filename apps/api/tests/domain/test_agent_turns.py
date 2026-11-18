from datetime import UTC, datetime
from decimal import Decimal

from jalada.modules.agent.domain.conversation import Message, Role, earlier_questions, title_from
from jalada.modules.agent.domain.run import AgentStep, Budget, Outcome, StepKind, TurnResult
from jalada.modules.pipeline.domain.model import ModelUsage


def test_a_short_question_is_its_own_title() -> None:
    assert title_from("  How much  did I pay KPLC? ") == "How much did I pay KPLC?"


def test_a_long_question_is_cut_at_a_word() -> None:
    title = title_from("word " * 40)

    assert title.endswith("word...")
    assert len(title) <= 83


def test_the_budget_stops_at_the_step_limit() -> None:
    budget = Budget(max_steps=2)

    assert budget.allows(1, ModelUsage())
    assert not budget.allows(2, ModelUsage())


def test_the_budget_stops_at_the_token_or_cost_limit() -> None:
    budget = Budget(max_tokens=100, max_cost_usd=Decimal("0.01"))

    assert not budget.allows(0, ModelUsage(input_tokens=100))
    assert not budget.allows(0, ModelUsage(cost_usd=Decimal("0.01")))


def test_a_turn_adds_up_what_its_steps_cost() -> None:
    steps = (
        AgentStep(StepKind.MODEL, "m", "tool", 10, ModelUsage(10, 5, Decimal("0.001"))),
        AgentStep(StepKind.TOOL, "search_entries", "ok", 3),
        AgentStep(StepKind.MODEL, "m", "answer", 10, ModelUsage(20, 5, Decimal("0.002"))),
    )

    usage = TurnResult("Done", Outcome.ANSWERED, steps).usage

    assert (usage.tokens, usage.cost_usd) == (40, Decimal("0.003"))


def test_earlier_questions_keep_only_what_the_person_asked() -> None:
    at = datetime(2026, 11, 18, tzinfo=UTC)
    older = [
        Message(Role.PERSON, "How much  did I pay KPLC?", at),
        Message(Role.ASSISTANT, "You paid Ksh 4,500.", at),
        Message(Role.PERSON, "And rent? " + "word " * 60, at),
    ]

    asked = earlier_questions(older)

    assert asked[0] == "How much did I pay KPLC?"
    assert asked[1].endswith("...") and len(asked[1]) <= 153
    assert len(asked) == 2


def test_only_the_last_earlier_questions_are_kept() -> None:
    at = datetime(2026, 11, 18, tzinfo=UTC)
    older = [Message(Role.PERSON, f"question {i}", at) for i in range(15)]

    assert earlier_questions(older, limit=3) == ("question 12", "question 13", "question 14")
