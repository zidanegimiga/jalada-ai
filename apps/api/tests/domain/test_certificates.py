import uuid
from dataclasses import replace
from datetime import date

from samples import certificate, confirmed_entry, deposit

from jalada.modules.ledger.domain.certificates import (
    expected_payment_cents,
    link_problem,
    search_window,
    suggest_payments,
)
from jalada.modules.ledger.domain.entries import EntryStatus

USER = uuid.uuid4()
# 40,000 gross with 5% withheld: the client pays 38,000.
CERTIFICATE = certificate(USER, date(2026, 3, 3), 4_000_000, 200_000, "EXAMPLE CLIENT LTD")


def test_the_expected_payment_is_gross_minus_tax() -> None:
    assert expected_payment_cents(CERTIFICATE) == 3_800_000
    assert search_window(CERTIFICATE) == (date(2025, 12, 3), date(2026, 5, 2))


def test_the_exact_amount_comes_first_then_the_same_payer_then_the_nearest_date() -> None:
    near_wrong_amount = deposit(USER, date(2026, 3, 3), 1_000_000, "EXAMPLE CLIENT LTD")
    exact_other_payer = deposit(USER, date(2026, 3, 1), 3_800_000, "BANK TRANSFER")
    exact_far = deposit(USER, date(2026, 4, 20), 3_800_000, "Example Client Ltd")
    exact_near = deposit(USER, date(2026, 3, 10), 3_800_000, "EXAMPLE  CLIENT LTD")

    ranked = suggest_payments(
        CERTIFICATE, [near_wrong_amount, exact_other_payer, exact_far, exact_near]
    )

    assert ranked == [exact_near, exact_far, exact_other_payer, near_wrong_amount]


def test_money_out_unconfirmed_entries_and_more_than_the_gross_are_never_suggested() -> None:
    out = confirmed_entry(USER, date(2026, 3, 3), 3_800_000, "out", "business_stock")
    waiting = replace(
        deposit(USER, date(2026, 3, 3), 3_800_000, "X"), status=EntryStatus.NEEDS_REVIEW
    )
    too_big = deposit(USER, date(2026, 3, 3), 4_000_001, "X")

    assert suggest_payments(CERTIFICATE, [out, waiting, too_big, CERTIFICATE]) == []


def test_only_five_suggestions_are_given() -> None:
    deposits = [deposit(USER, date(2026, 3, day), 100_000, "X") for day in range(1, 10)]

    assert len(suggest_payments(CERTIFICATE, deposits)) == 5


def test_payments_cannot_add_up_to_more_than_the_gross_amount() -> None:
    first = deposit(USER, date(2026, 3, 3), 2_000_000, "X")
    second = deposit(USER, date(2026, 3, 4), 2_000_001, "X")

    assert link_problem(CERTIFICATE, first, 0) is None
    assert link_problem(CERTIFICATE, second, 2_000_000) is not None
    assert link_problem(CERTIFICATE, CERTIFICATE, 0) is not None


def test_once_part_is_linked_only_what_is_left_can_be_suggested() -> None:
    rest = deposit(USER, date(2026, 3, 9), 1_800_000, "X")
    too_big = deposit(USER, date(2026, 3, 8), 2_100_000, "X")
    small = deposit(USER, date(2026, 3, 4), 500_000, "X")

    assert suggest_payments(CERTIFICATE, [too_big, small, rest], linked_cents=2_000_000) == [
        rest,
        small,
    ]
    assert suggest_payments(CERTIFICATE, [small], linked_cents=4_000_000) == []
