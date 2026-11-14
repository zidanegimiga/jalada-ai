import uuid
from dataclasses import replace
from datetime import date

import pytest
from samples import confirmed_entry

from jalada.modules.ledger.domain.categories import Direction
from jalada.modules.ledger.domain.matching import is_exact_match
from jalada.modules.ledger.domain.transactions import (
    EvidenceRole,
    Transaction,
    TransactionStatus,
    from_entry,
)

DAY = date(2026, 11, 13)


def payment(code: str = "UK7XY2AB34") -> Transaction:
    entry = replace(
        confirmed_entry(uuid.uuid4(), DAY, 35000, "out", "personal_food"), mpesa_code=code
    )
    return from_entry(entry, None, EvidenceRole.PAYMENT_PROOF)


def test_the_same_code_amount_direction_and_date_is_the_same_payment() -> None:
    assert is_exact_match(payment(), "UK7XY2AB34", 35000, Direction.OUT, DAY)
    assert is_exact_match(payment(), "UK7XY2AB34", 35000, Direction.OUT), "a date may be missing"


@pytest.mark.parametrize(
    ("code", "cents", "direction", "day"),
    [
        ("UK7XY2AB35", 35000, Direction.OUT, DAY),  # another code
        ("uk7xy2ab34", 35000, Direction.OUT, DAY),  # misread: not the right shape
        ("UK7XY2AB3", 35000, Direction.OUT, DAY),  # misread: too short
        (None, 35000, Direction.OUT, DAY),
        ("UK7XY2AB34", 35100, Direction.OUT, DAY),  # another amount
        ("UK7XY2AB34", None, Direction.OUT, DAY),
        ("UK7XY2AB34", 35000, Direction.IN, DAY),  # the other way
        ("UK7XY2AB34", 35000, None, DAY),
        ("UK7XY2AB34", 35000, Direction.OUT, date(2026, 11, 14)),  # another day
    ],
)
def test_anything_less_is_not_an_exact_match(
    code: str | None, cents: int | None, direction: Direction | None, day: date
) -> None:
    assert not is_exact_match(payment(), code, cents, direction, day)


def test_a_rejected_payment_is_never_matched() -> None:
    rejected = replace(payment(), status=TransactionStatus.REJECTED)

    assert not is_exact_match(rejected, "UK7XY2AB34", 35000, Direction.OUT, DAY)
