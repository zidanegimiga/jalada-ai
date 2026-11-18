from decimal import Decimal

import pytest

from jalada.modules.agent.domain.grounding import amounts, promises_a_change, ungrounded

RESULT = '{"total": "4500.00", "count": 3, "from": "2026-07-01", "to": "2026-09-30"}'


def test_the_same_amount_written_differently_is_one_amount() -> None:
    assert amounts("KES 1,500 or 1500.00 or Ksh1500") == {Decimal(1500)}


def test_small_whole_numbers_are_not_amounts() -> None:
    assert amounts("3 payments on the 15th") == set()


def test_decimals_currencies_and_large_numbers_are_amounts() -> None:
    assert amounts("Ksh 50 and 2.5 and 250") == {Decimal(50), Decimal("2.5"), Decimal(250)}


def test_an_answer_with_amounts_from_the_records_is_grounded() -> None:
    assert ungrounded("You paid KPLC Ksh 4,500 over 3 payments.", [RESULT]) == []


def test_an_amount_no_tool_gave_is_caught() -> None:
    assert ungrounded("You paid Ksh 4,800 this quarter.", [RESULT]) == [Decimal(4800)]


def test_dates_in_the_answer_match_dates_in_the_records() -> None:
    assert ungrounded("Between 1 July 2026 and 30 September 2026.", [RESULT]) == []


def test_an_answer_with_no_amounts_needs_no_records() -> None:
    assert ungrounded("I could not find any payments to KPLC.", []) == []


def test_digits_inside_an_id_do_not_count_as_an_amount() -> None:
    result = '{"id": "0f3a2b1c-4500-4d2e-9f00-123456789abc", "total": "120.00"}'

    assert ungrounded("You paid Ksh 4,500.", [result]) == [Decimal(4500)]


@pytest.mark.parametrize(
    ("answer", "promises"),
    [
        ("Please confirm the change by tapping on the screen.", True),
        ("I have suggested moving it to Workspace rent.", True),
        ("Tap Confirm to change it.", True),
        ("Nothing is waiting for you to check.", False),
        ("I cannot confirm what you owe KRA.", False),
    ],
)
def test_an_answer_that_says_a_change_is_waiting_is_noticed(answer: str, promises: bool) -> None:
    assert promises_a_change(answer) is promises
