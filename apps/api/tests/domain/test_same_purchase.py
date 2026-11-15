import uuid
from dataclasses import replace
from datetime import UTC, date, datetime
from typing import Any

import pytest

from jalada.modules.ledger.domain.categories import Direction, Purpose
from jalada.modules.ledger.domain.same_purchase import names_alike, same_purchase
from jalada.modules.ledger.domain.transactions import (
    EvidenceLink,
    EvidenceRole,
    LinkedBy,
    Transaction,
    TransactionKind,
    TransactionLine,
    TransactionStatus,
)

USER = uuid.uuid4()
DAY = date(2026, 11, 7)
NOW = datetime(2026, 11, 7, 12, tzinfo=UTC)


def record(status: TransactionStatus, counterparty: str | None, role: EvidenceRole) -> Transaction:
    return Transaction(
        id=uuid.uuid4(),
        user_id=USER,
        account_id=None,
        kind=TransactionKind.PAYMENT,
        status=status,
        occurred_on=DAY,
        direction=Direction.OUT,
        amount_cents=235000,
        counterparty=counterparty,
        reference=None,
        payment_code=None,
        confidence=0.9,
        run_id=None,
        created_at=NOW,
        confirmed_at=None,
        lines=(TransactionLine(235000, None, Purpose.UNSURE),),
        evidence=(EvidenceLink(uuid.uuid4(), role, LinkedBy.PIPELINE, NOW),),
    )


def receipt(counterparty: str | None = "SAMPLE MART WESTGATE") -> Transaction:
    return record(TransactionStatus.CANDIDATE, counterparty, EvidenceRole.RECEIPT)


def payment(counterparty: str | None = "SAMPLE MART LTD") -> Transaction:
    return record(TransactionStatus.NEEDS_REVIEW, counterparty, EvidenceRole.PAYMENT_PROOF)


def test_same_amount_day_and_name_is_a_strong_suggestion() -> None:
    assert same_purchase(receipt(), payment()) == (
        1.0,
        ("same amount", "same day", "similar name"),
    )


def test_a_date_a_few_days_off_still_counts() -> None:
    later = replace(payment("OTHER NAME"), occurred_on=date(2026, 11, 9))

    assert same_purchase(receipt(), later) == (0.7, ("same amount", "2 days apart"))


def test_without_dates_a_similar_name_is_enough() -> None:
    undated = replace(receipt(), occurred_on=None)

    assert same_purchase(undated, payment()) == (0.7, ("same amount", "similar name"))


def test_the_amount_alone_is_not_enough() -> None:
    undated = replace(receipt(), occurred_on=None)

    assert same_purchase(undated, payment("SOMEONE ELSE")) is None


@pytest.mark.parametrize(
    "changes",
    [
        {"amount_cents": 235100},
        {"amount_cents": None},
        {"occurred_on": date(2026, 11, 11)},
        {"direction": Direction.IN},
        {"status": TransactionStatus.REJECTED},
        {"status": TransactionStatus.CANDIDATE},
        {"kind": TransactionKind.TRANSFER},
    ],
)
def test_a_payment_that_cannot_be_the_purchase_is_never_suggested(changes: dict[str, Any]) -> None:
    assert same_purchase(receipt(), replace(payment(), **changes)) is None


def test_a_payment_that_has_its_receipt_is_not_offered_another() -> None:
    other = EvidenceLink(uuid.uuid4(), EvidenceRole.RECEIPT, LinkedBy.SUGGESTED, NOW)
    paid = payment()
    with_receipt = replace(paid, evidence=(*paid.evidence, other))

    assert same_purchase(receipt(), with_receipt) is None


def test_only_a_candidate_is_matched_to_a_payment() -> None:
    assert same_purchase(payment(), payment()) is None


def test_a_confirmed_payment_can_still_get_its_receipt() -> None:
    confirmed = replace(payment(), status=TransactionStatus.CONFIRMED)

    assert same_purchase(receipt(), confirmed) is not None


@pytest.mark.parametrize(
    ("first", "second"),
    [
        ("DUKA BORA LTD", "Duka Bora Supermarket Westlands"),
        ("Till 512345", "BUY GOODS 512345 SAMPLE"),
        ("MUTHAIGAA STORES", "MUTHAIGA"),
    ],
)
def test_names_are_alike_by_word_till_number_or_spelling(first: str, second: str) -> None:
    assert names_alike(first, second, 0.6)


def test_common_words_do_not_make_names_alike() -> None:
    assert not names_alike("ALPHA ENTERPRISES LTD", "OMEGA ENTERPRISES LTD", 0.6)
