import uuid
from dataclasses import replace
from datetime import UTC, date, datetime

import pytest
from samples import confirmed_entry

from jalada.modules.ledger.domain.categories import Direction, Purpose
from jalada.modules.ledger.domain.entries import Correction, EntryStatus
from jalada.modules.ledger.domain.payment_review import ReviewProblem, confirmed, corrected
from jalada.modules.ledger.domain.transactions import (
    EvidenceRole,
    Transaction,
    TransactionLine,
    TransactionStatus,
    from_entry,
)

NOW = datetime(2026, 11, 14, 9, 0, tzinfo=UTC)


def proposed(category: str | None = None) -> Transaction:
    entry = replace(
        confirmed_entry(uuid.uuid4(), date(2026, 11, 4), 15000, "out", "personal_food"),
        status=EntryStatus.PROPOSED,
        category=category,
        purpose=Purpose.UNSURE,
        confirmed_at=None,
    )
    return from_entry(entry, None, EvidenceRole.PAYMENT_PROOF)


def test_a_correction_changes_the_payment_and_its_one_line() -> None:
    changed = corrected(
        proposed(),
        Correction(amount_cents=16000, counterparty="  JANE   WANJIKU ", category="personal_food"),
    )

    assert changed.amount_cents == 16000
    assert changed.counterparty == "JANE WANJIKU"
    assert changed.lines == (TransactionLine(16000, "personal_food", Purpose.UNSURE),)


def test_confirming_takes_the_purpose_from_the_category() -> None:
    done = confirmed(proposed("business_stock"), NOW)

    assert done.status == TransactionStatus.CONFIRMED
    assert done.confirmed_at == NOW
    assert done.lines[0].purpose == Purpose.BUSINESS


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (Correction(category="nonsense"), "That category does not exist."),
        (Correction(amount_cents=0), "The amount must be more than zero."),
    ],
)
def test_bad_corrections_are_refused(change: Correction, message: str) -> None:
    with pytest.raises(ReviewProblem, match=message):
        corrected(proposed(), change)


def test_confirming_needs_every_field_and_a_fitting_category() -> None:
    with pytest.raises(ReviewProblem, match="Add the category before confirming."):
        confirmed(proposed(), NOW)
    blank = replace(proposed("personal_food"), occurred_on=None, direction=None)
    with pytest.raises(ReviewProblem, match="Add the date, direction before confirming."):
        confirmed(blank, NOW)
    with pytest.raises(ReviewProblem, match="does not fit money going this way"):
        confirmed(replace(proposed("salary"), direction=Direction.OUT), NOW)


def test_a_split_payment_is_changed_line_by_line() -> None:
    split = replace(
        proposed(),
        lines=(
            TransactionLine(10000, "personal_food", Purpose.PERSONAL),
            TransactionLine(5000, "business_stock", Purpose.BUSINESS),
        ),
    )

    assert corrected(split, Correction(counterparty="SHOP")).counterparty == "SHOP"
    with pytest.raises(ReviewProblem, match="one line at a time"):
        corrected(split, Correction(category="personal_food"))
    done = confirmed(split, NOW)
    assert [line.purpose for line in done.lines] == [Purpose.PERSONAL, Purpose.BUSINESS]
