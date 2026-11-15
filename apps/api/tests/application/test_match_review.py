"""Answering "Is this the same purchase?" on To check."""

import uuid

import pytest
from fakes import FakeUnitOfWork, FixedClock, Store
from receipts import RECEIPT, USER, Send

from jalada.modules.evidence.domain.evidence import EvidenceStatus
from jalada.modules.ledger.application.entry_review import EntryReview
from jalada.modules.ledger.application.match_review import MatchReview
from jalada.modules.ledger.application.suggesting import suggest_same_purchase
from jalada.modules.ledger.domain.audit import AuditAction
from jalada.modules.ledger.domain.suggestions import SuggestionStatus
from jalada.modules.ledger.domain.transactions import (
    EvidenceRole,
    LinkedBy,
    Transaction,
    TransactionStatus,
)
from jalada.shared.errors import SuggestionNotFound


@pytest.fixture
def matches(store: Store, clock: FixedClock) -> MatchReview:
    return MatchReview(lambda: FakeUnitOfWork(store), clock)


@pytest.fixture
def asked(send: Send, store: Store) -> uuid.UUID:
    """A receipt, then its payment message: one open suggestion."""
    send("receipt")
    send("message")
    [suggestion] = store.suggestions.values()
    return suggestion.id


def by_status(store: Store, status: TransactionStatus) -> list[Transaction]:
    return [t for t in store.transactions.values() if t.status == status]


def test_to_check_asks_the_question_instead_of_showing_the_payment(
    asked: uuid.UUID, store: Store, review: EntryReview
) -> None:
    [item] = review.queue(USER)

    assert item.match is not None and item.match.suggestion.id == asked
    assert item.entry is not None and item.entry.id == store.suggestions[asked].payment_id
    assert item.match.candidate.counterparty == "SAMPLE MUSIC SHOP"
    assert item.match.receipt.id == item.match.candidate.evidence[0].evidence_id


def test_yes_moves_the_receipt_onto_the_payment(
    asked: uuid.UUID, store: Store, matches: MatchReview, review: EntryReview
) -> None:
    [candidate] = by_status(store, TransactionStatus.CANDIDATE)
    receipt_id = candidate.evidence[0].evidence_id

    payment = matches.accept(USER, asked)

    paid = store.transactions[payment.id]
    assert paid.status != TransactionStatus.CONFIRMED, "the user still confirms it"
    [_, link] = paid.evidence
    assert (link.evidence_id, link.role, link.linked_by) == (
        receipt_id,
        EvidenceRole.RECEIPT,
        LinkedBy.SUGGESTED,
    )
    assert store.transactions[candidate.id].status == TransactionStatus.MERGED
    assert store.evidence[receipt_id].status == EvidenceStatus.LINKED
    assert store.suggestions[asked].status == SuggestionStatus.ACCEPTED
    actions = {e.subject_id: e.action for e in store.audit_events if e.action != "proposed"}
    assert actions == {paid.id: AuditAction.LINKED, candidate.id: AuditAction.MERGED}
    [item] = review.queue(USER)
    assert item.match is None and item.entry is not None and item.entry.id == paid.id


def test_no_is_kept_and_never_asked_again(
    asked: uuid.UUID, store: Store, matches: MatchReview, review: EntryReview
) -> None:
    matches.decline(USER, asked)

    assert store.suggestions[asked].status == SuggestionStatus.DECLINED
    [candidate] = by_status(store, TransactionStatus.CANDIDATE)
    [item] = review.queue(USER)
    assert item.match is None, "the payment is back as itself"
    with FakeUnitOfWork(store) as work:
        assert suggest_same_purchase(work, candidate, FixedClock().now()) == []


def test_yes_to_one_receipt_closes_the_question_about_another(
    send: Send, store: Store, matches: MatchReview, review: EntryReview
) -> None:
    send("receipt")
    send("receipt", {**RECEIPT, "counterparty": "ANOTHER SHOP"})
    send("message")
    first, second = store.suggestions.values()

    matches.accept(USER, first.id)

    assert store.suggestions[second.id].status == SuggestionStatus.CLOSED
    assert all(item.match is None for item in review.queue(USER))


def test_a_question_is_answered_once_and_only_by_its_owner(
    asked: uuid.UUID, matches: MatchReview
) -> None:
    with pytest.raises(SuggestionNotFound):
        matches.accept(uuid.uuid4(), asked)
    matches.decline(USER, asked)
    with pytest.raises(SuggestionNotFound):
        matches.accept(USER, asked)
