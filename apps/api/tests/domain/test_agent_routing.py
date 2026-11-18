import pytest

from jalada.modules.agent.domain.routing import Route, route_for


@pytest.mark.parametrize(
    "question",
    [
        "How much did I pay KPLC?",
        "Is anything waiting for me to check?",
        "Can I get last year's workbook?",
        "What did I spend on food this month?",
    ],
)
def test_single_lookups_take_the_fast_route(question: str) -> None:
    assert route_for(question) == Route.FAST


@pytest.mark.parametrize(
    "question",
    [
        "Compare my spending in July and August.",
        "Why was October so expensive?",
        "Show me a breakdown of costs for each month this year",
        "How much did I spend between March and June?",
        "How much on KPLC? And on rent?",
        "Tell me " + "about my payments " * 12,
    ],
)
def test_comparisons_reasons_and_several_questions_take_the_deep_route(question: str) -> None:
    assert route_for(question) == Route.DEEP
