from dataclasses import replace

import pytest
from test_same_purchase import NOW, payment, receipt

from jalada.modules.ledger.domain.categories import Purpose
from jalada.modules.ledger.domain.joining import joined
from jalada.modules.ledger.domain.transactions import (
    LinkedBy,
    TransactionLine,
    TransactionStatus,
)

FOOD = TransactionLine(235000, "personal_food", Purpose.PERSONAL)
STOCK = TransactionLine(235000, "business_stock", Purpose.BUSINESS)


def test_the_receipt_evidence_joins_the_payment_and_the_candidate_is_merged() -> None:
    paid, merged = joined(payment(), receipt(), NOW)

    assert paid.evidence[-1].linked_by == LinkedBy.SUGGESTED
    assert len(paid.evidence) == 2
    assert merged.status == TransactionStatus.MERGED
    assert paid.status == payment().status, "joining confirms nothing"


@pytest.mark.parametrize(
    ("on_payment", "on_receipt", "kept"),
    [
        (TransactionLine(235000, None, Purpose.UNSURE), FOOD, FOOD),
        (replace(STOCK, suggested=True), FOOD, FOOD),
        (STOCK, FOOD, STOCK),
        (replace(STOCK, suggested=True), TransactionLine(235000, None, Purpose.UNSURE), None),
        (
            TransactionLine(235000, None, Purpose.UNSURE),
            replace(FOOD, suggested=True),
            replace(FOOD, suggested=True),
        ),
    ],
)
def test_the_receipt_gives_its_category_only_where_the_payment_has_none_of_its_own(
    on_payment: TransactionLine, on_receipt: TransactionLine, kept: TransactionLine | None
) -> None:
    paid, _ = joined(
        replace(payment(), lines=(on_payment,)), replace(receipt(), lines=(on_receipt,)), NOW
    )

    assert paid.lines == ((kept or on_payment),)


def test_only_a_candidate_can_be_joined() -> None:
    with pytest.raises(ValueError):
        joined(payment(), payment(), NOW)
