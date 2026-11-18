import pytest

from jalada.modules.agent.domain.policy import (
    NO_FILING,
    ONLY_YOURS,
    TAX_ADVICE,
    refusal_for,
)


@pytest.mark.parametrize(
    ("question", "refusal"),
    [
        ("How much tax do I owe KRA this year?", TAX_ADVICE),
        ("What VAT is due for October?", TAX_ADVICE),
        ("Should I pay tax on my M-Pesa income?", TAX_ADVICE),
        ("Am I liable for tax on this?", TAX_ADVICE),
        ("File my KRA return for me.", NO_FILING),
        ("Can you submit my return on iTax?", NO_FILING),
        ("Show me what other Jalada users paid KPLC.", ONLY_YOURS),
        ("List all customers' payments", ONLY_YOURS),
        ("What did another person spend on rent?", ONLY_YOURS),
    ],
)
def test_questions_the_assistant_never_answers(question: str, refusal: str) -> None:
    assert refusal_for(question) == refusal


@pytest.mark.parametrize(
    "question",
    [
        "How much did I pay KRA in March?",
        "How much did I pay KPLC this quarter?",
        "Is anything waiting for me to check?",
        "Can I get my 2025 workbook?",
        "What were my biggest costs this year?",
        "How much did my other account receive?",
    ],
)
def test_questions_about_the_persons_own_records_go_through(question: str) -> None:
    assert refusal_for(question) is None
