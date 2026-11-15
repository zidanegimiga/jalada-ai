"""A receipt whose payment never arrived is asked about after three days: paid in cash or by
card? (design 03, "Candidates")."""

from datetime import timedelta

import pytest
from fakes import FakeUnitOfWork, FixedClock, Store
from receipts import USER, Send

from jalada.modules.evidence.domain.evidence import EvidenceStatus
from jalada.modules.ledger.application.entry_review import EntryReview
from jalada.modules.ledger.application.how_paid import HowPaid
from jalada.modules.ledger.application.match_review import MatchReview
from jalada.modules.ledger.domain.audit import AuditAction
from jalada.modules.ledger.domain.how_paid import PaidWith
from jalada.modules.ledger.domain.money_accounts import MoneyAccountKind, default_accounts
from jalada.modules.ledger.domain.transactions import TransactionStatus
from jalada.shared.errors import InvalidEntry

LATER = timedelta(days=3)


@pytest.fixture
def how_paid(store: Store, clock: FixedClock) -> HowPaid:
    for account in default_accounts(USER, clock.now()):
        store.money_accounts[account.id] = account
    return HowPaid(lambda: FakeUnitOfWork(store), clock)


def waited(send: Send, clock: FixedClock) -> None:
    send("receipt")
    clock.current += LATER


def test_a_receipt_is_not_asked_about_too_soon(
    send: Send, clock: FixedClock, review: EntryReview
) -> None:
    send("receipt")
    clock.current += LATER - timedelta(hours=1)

    assert review.queue(USER) == []


def test_after_three_days_to_check_asks_how_it_was_paid(
    send: Send, clock: FixedClock, store: Store, review: EntryReview
) -> None:
    waited(send, clock)

    [item] = review.queue(USER)
    [candidate] = store.transactions.values()
    assert item.ask_how_paid and item.match is None
    assert item.entry is not None and item.entry.id == candidate.id
    assert item.entry.amount_cents == 41900


def test_cash_puts_it_on_the_cash_account_to_confirm(
    send: Send, clock: FixedClock, store: Store, review: EntryReview, how_paid: HowPaid
) -> None:
    waited(send, clock)
    [candidate] = store.transactions.values()

    how_paid.answer(USER, candidate.id, PaidWith.CASH)

    paid = store.transactions[candidate.id]
    [cash] = [a for a in store.money_accounts.values() if a.kind == MoneyAccountKind.CASH]
    assert (paid.account_id, paid.status) == (cash.id, TransactionStatus.NEEDS_REVIEW)
    receipt_id = paid.evidence[0].evidence_id
    assert store.evidence[receipt_id].status == EvidenceStatus.NEEDS_REVIEW
    assert store.audit_events[-1].action == AuditAction.ANSWERED
    [item] = review.queue(USER)
    assert not item.ask_how_paid, "now it is a payment to confirm"


def test_card_opens_a_card_account_once(
    send: Send, clock: FixedClock, store: Store, how_paid: HowPaid
) -> None:
    send("receipt")
    send("receipt")
    clock.current += LATER

    for candidate in list(store.transactions.values()):
        how_paid.answer(USER, candidate.id, PaidWith.CARD)

    cards = [a for a in store.money_accounts.values() if a.kind == MoneyAccountKind.CARD]
    assert [card.name for card in cards] == ["Card"]
    assert {t.account_id for t in store.transactions.values()} == {cards[0].id}


def test_a_receipt_is_answered_once(
    send: Send, clock: FixedClock, store: Store, how_paid: HowPaid
) -> None:
    waited(send, clock)
    [candidate] = store.transactions.values()
    how_paid.answer(USER, candidate.id, PaidWith.CASH)

    with pytest.raises(InvalidEntry):
        how_paid.answer(USER, candidate.id, PaidWith.CARD)


def test_a_suggested_match_is_asked_first_and_a_no_brings_the_question_back(
    send: Send, clock: FixedClock, store: Store, review: EntryReview
) -> None:
    send("receipt")
    send("message")
    clock.current += LATER

    [item] = review.queue(USER)
    assert item.match is not None and not item.ask_how_paid

    MatchReview(lambda: FakeUnitOfWork(store), clock).decline(USER, item.match.suggestion.id)

    assert any(item.ask_how_paid for item in review.queue(USER))
