import uuid
from dataclasses import replace
from datetime import timedelta

import pytest
from test_same_purchase import NOW, payment, receipt

from jalada.modules.ledger.domain.how_paid import paid_from, time_to_ask
from jalada.modules.ledger.domain.transactions import TransactionStatus

THREE_DAYS = timedelta(days=3)


def test_a_receipt_is_asked_about_after_three_days_with_nothing_offered() -> None:
    assert not time_to_ask(receipt(), NOW + THREE_DAYS - timedelta(minutes=1), False)
    assert time_to_ask(receipt(), NOW + THREE_DAYS, False)


def test_an_open_suggestion_is_asked_first() -> None:
    assert not time_to_ask(receipt(), NOW + THREE_DAYS, True)


def test_only_a_candidate_is_asked_how_it_was_paid() -> None:
    assert not time_to_ask(payment(), NOW + THREE_DAYS, False)


def test_the_answer_puts_it_on_the_account_and_waits_for_the_user() -> None:
    account = uuid.uuid4()

    paid = paid_from(receipt(), account)

    assert (paid.account_id, paid.status) == (account, TransactionStatus.NEEDS_REVIEW)
    assert paid.lines == receipt().lines and paid.amount_cents == receipt().amount_cents
    with pytest.raises(ValueError):
        paid_from(replace(receipt(), status=TransactionStatus.MERGED), account)
