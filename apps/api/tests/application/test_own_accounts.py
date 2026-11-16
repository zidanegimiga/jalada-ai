"""Asking once whether a paybill is the user's own account (design 03, "Moved M-Pesa to
the bank")."""

import uuid

import pytest
from fakes import FakeUnitOfWork, FixedClock, Store
from receipts import USER
from transfers import AGAIN, FROM_BANK, FROM_BANK_AGAIN, OTHER_ACCOUNT, TO_BANK, Paste

from jalada.modules.ledger.application.entry_review import EntryReview
from jalada.modules.ledger.application.own_accounts import OwnAccounts
from jalada.modules.ledger.domain.audit import AuditAction
from jalada.modules.ledger.domain.entries import Correction
from jalada.modules.ledger.domain.money_accounts import MoneyAccountKind
from jalada.modules.ledger.domain.transactions import TransactionKind
from jalada.shared.errors import EntryNotFound, InvalidEntry


@pytest.fixture
def own(store: Store, clock: FixedClock) -> OwnAccounts:
    return OwnAccounts(lambda: FakeUnitOfWork(store), clock)


def test_a_payment_to_a_bank_paybill_is_asked_about(paste: Paste, review: EntryReview) -> None:
    paste(TO_BANK)

    [item] = review.queue(USER)
    assert item.ask_own_account


def test_yes_makes_it_a_transfer_to_a_new_account(
    paste: Paste, own: OwnAccounts, store: Store, review: EntryReview
) -> None:
    payment_id = paste(TO_BANK)

    entry = own.say_mine(USER, payment_id)

    assert entry.category == "own_transfer_out"
    transfer = store.transactions[payment_id]
    account = store.money_accounts[transfer.to_account_id] if transfer.to_account_id else None
    assert transfer.kind == TransactionKind.TRANSFER
    assert account is not None and account.kind == MoneyAccountKind.BANK
    assert account.name == "SAMPLE BANK PAYBILL ending 6789"
    assert account.identifiers == {"paybill": "sample bank paybill", "account": "0123456789"}
    assert store.audit_events[-1].action == AuditAction.ANSWERED
    [item] = review.queue(USER)
    assert not item.ask_own_account


def test_yes_covers_waiting_payments_to_the_same_account_only(
    paste: Paste, own: OwnAccounts, store: Store
) -> None:
    first, again, other = paste(TO_BANK), paste(AGAIN), paste(OTHER_ACCOUNT)

    own.say_mine(USER, first)

    kinds = [store.transactions[t].kind for t in (first, again, other)]
    assert kinds == [TransactionKind.TRANSFER, TransactionKind.TRANSFER, TransactionKind.PAYMENT]
    assert len([a for a in store.money_accounts.values() if a.user_id == USER]) == 1


def test_answering_twice_keeps_one_account(paste: Paste, own: OwnAccounts, store: Store) -> None:
    first = paste(TO_BANK)
    own.say_mine(USER, first)
    other = paste(OTHER_ACCOUNT)

    own.say_mine(USER, other)

    banks = [a for a in store.money_accounts.values() if a.kind == MoneyAccountKind.BANK]
    assert sorted(a.name for a in banks) == [
        "SAMPLE BANK PAYBILL ending 3210",
        "SAMPLE BANK PAYBILL ending 6789",
    ]


def test_a_category_chosen_by_the_user_stops_the_question(
    paste: Paste, review: EntryReview
) -> None:
    payment_id = paste(TO_BANK)
    review.confirm(USER, payment_id, Correction(category="business_rent"))

    paste(AGAIN)

    [item] = review.queue(USER)
    assert not item.ask_own_account


def test_only_a_waiting_paybill_payment_can_be_answered(
    paste: Paste, own: OwnAccounts, review: EntryReview
) -> None:
    payment_id = paste(TO_BANK)
    review.confirm(USER, payment_id, Correction(category="business_rent"))

    with pytest.raises(InvalidEntry):
        own.say_mine(USER, payment_id)
    with pytest.raises(EntryNotFound):
        own.say_mine(uuid.uuid4(), payment_id)


def test_later_payments_to_the_account_arrive_as_ready_transfers(
    paste: Paste, own: OwnAccounts, store: Store, review: EntryReview
) -> None:
    first = paste(TO_BANK)
    own.say_mine(USER, first)
    review.confirm(USER, first)

    later = paste(AGAIN)

    transfer = store.transactions[later]
    assert transfer.kind == TransactionKind.TRANSFER
    assert transfer.to_account_id == store.transactions[first].to_account_id
    [item] = review.queue(USER)
    assert item.ready and not item.ask_own_account
    assert item.entry is not None and item.entry.category == "own_transfer_out"


def test_another_account_at_the_same_paybill_is_still_asked_about(
    paste: Paste, own: OwnAccounts, review: EntryReview
) -> None:
    own.say_mine(USER, paste(TO_BANK))

    paste(OTHER_ACCOUNT)

    asked = [item.ask_own_account for item in review.queue(USER)]
    assert asked == [False, True]


def test_money_in_from_a_bank_is_asked_about(paste: Paste, review: EntryReview) -> None:
    paste(FROM_BANK)

    [item] = review.queue(USER)
    assert item.ask_own_account


def test_yes_makes_money_in_from_a_bank_a_transfer(
    paste: Paste, own: OwnAccounts, store: Store, review: EntryReview
) -> None:
    payment_id = paste(FROM_BANK)

    entry = own.say_mine(USER, payment_id)

    assert entry.category == "own_transfer"
    transfer = store.transactions[payment_id]
    account = store.money_accounts[transfer.to_account_id] if transfer.to_account_id else None
    assert transfer.kind == TransactionKind.TRANSFER
    assert account is not None and account.name == "SAMPLE BANK 303030"
    assert account.identifiers == {"sender": "sample bank 303030"}
    review.confirm(USER, payment_id)

    later = paste(FROM_BANK_AGAIN)

    assert store.transactions[later].kind == TransactionKind.TRANSFER
    assert store.transactions[later].to_account_id == account.id
    [item] = review.queue(USER)
    assert item.ready and not item.ask_own_account
