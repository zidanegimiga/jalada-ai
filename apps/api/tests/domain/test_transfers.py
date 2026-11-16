import uuid
from dataclasses import replace
from datetime import UTC, date, datetime

import pytest

from jalada.modules.ledger.domain.categories import Direction, Purpose
from jalada.modules.ledger.domain.money_accounts import MoneyAccount, MoneyAccountKind
from jalada.modules.ledger.domain.transactions import (
    EvidenceLink,
    EvidenceRole,
    LinkedBy,
    Transaction,
    TransactionKind,
    TransactionLine,
    TransactionStatus,
)
from jalada.modules.ledger.domain.transfers import (
    account_name,
    as_transfer,
    may_be_own_account,
    own_account_for,
    own_identifiers,
)

NOW = datetime(2026, 11, 6, 9, tzinfo=UTC)
USER = uuid.uuid4()


def paid(
    counterparty: str | None = "SAMPLE BANK PAYBILL", reference: str | None = "0123 456789"
) -> Transaction:
    return Transaction(
        id=uuid.uuid4(),
        user_id=USER,
        account_id=uuid.uuid4(),
        kind=TransactionKind.PAYMENT,
        status=TransactionStatus.NEEDS_REVIEW,
        occurred_on=date(2026, 11, 6),
        direction=Direction.OUT,
        amount_cents=500000,
        counterparty=counterparty,
        reference=reference,
        payment_code="UK6CC1CC11",
        confidence=0.0,
        run_id=None,
        created_at=NOW,
        confirmed_at=None,
        lines=(TransactionLine(500000, None, Purpose.UNSURE),),
        evidence=(EvidenceLink(uuid.uuid4(), EvidenceRole.PAYMENT_PROOF, LinkedBy.PIPELINE, NOW),),
    )


def bank(identifiers: dict[str, str]) -> MoneyAccount:
    return MoneyAccount(uuid.uuid4(), USER, MoneyAccountKind.BANK, "Bank", False, NOW, identifiers)


def test_a_paybill_is_known_by_its_name_and_account_number() -> None:
    assert own_identifiers(paid()) == {
        "paybill": "sample bank paybill",
        "account": "0123456789",
    }


@pytest.mark.parametrize(
    "payment",
    [
        paid(reference=None),
        replace(paid(), kind=TransactionKind.TRANSFER),
        replace(paid("JANE DOE 0712345678"), direction=Direction.IN),
        replace(paid(None), direction=Direction.IN),
    ],
)
def test_only_paybills_and_business_senders_have_one(payment: Transaction) -> None:
    assert own_identifiers(payment) is None
    assert not may_be_own_account(payment)


@pytest.mark.parametrize(
    "name", ["SAMPLE BANK PAYBILL", "Sample Sacco", "SAMPLE MMF", "KCB Paybill", "I&M SAMPLE"]
)
def test_banks_and_savings_may_be_the_users_own(name: str) -> None:
    assert may_be_own_account(paid(name))


@pytest.mark.parametrize("name", ["SAMPLE MUSIC SHOP", "BANKSIDE HARDWARE", "KPLC PREPAID"])
def test_shops_and_bills_are_not_asked_about(name: str) -> None:
    assert not may_be_own_account(paid(name))


def test_a_known_account_must_match_name_and_number() -> None:
    mine = bank({"paybill": "sample bank paybill", "account": "0123456789"})
    someone_else = paid(reference="999")

    assert own_account_for(paid(), [mine]) == mine
    assert own_account_for(someone_else, [mine]) is None


def test_a_transfer_goes_to_the_account_and_is_not_spending() -> None:
    mine = bank({"paybill": "sample bank paybill", "account": "0123456789"})

    transfer = as_transfer(paid(), mine)

    assert (transfer.kind, transfer.to_account_id) == (TransactionKind.TRANSFER, mine.id)
    assert transfer.lines == (TransactionLine(500000, "own_transfer_out", Purpose.PERSONAL),)


def test_the_account_is_named_by_its_last_digits() -> None:
    name = account_name({"account": "0123456789"}, "SAMPLE  BANK PAYBILL")

    assert name == "SAMPLE BANK PAYBILL ending 6789"


def received(counterparty: str = "SAMPLE BANK 303030") -> Transaction:
    return replace(paid(counterparty, None), direction=Direction.IN)


def test_money_in_from_a_business_is_known_by_its_name() -> None:
    assert own_identifiers(received()) == {"sender": "sample bank 303030"}


def test_money_in_from_a_bank_may_be_the_users_own() -> None:
    assert may_be_own_account(received())
    assert not may_be_own_account(received("SAMPLE TRADERS 303030"))


def test_money_in_from_the_account_is_a_transfer_and_not_income() -> None:
    mine = bank({"sender": "sample bank 303030"})

    transfer = as_transfer(received(), mine)

    assert own_account_for(received(), [mine]) == mine
    assert (transfer.kind, transfer.to_account_id) == (TransactionKind.TRANSFER, mine.id)
    assert transfer.lines == (TransactionLine(500000, "own_transfer", Purpose.PERSONAL),)


def test_a_sender_is_named_as_it_is_written() -> None:
    assert account_name({"sender": "sample bank 303030"}, "SAMPLE  BANK 303030") == (
        "SAMPLE BANK 303030"
    )
