"""Taking back "Yes, same purchase"."""

import uuid

import pytest
from fakes import FakeUnitOfWork, FixedClock, Store
from receipts import RECEIPT, USER, Send

from jalada.modules.evidence.domain.evidence import EvidenceStatus
from jalada.modules.ledger.application.entry_review import EntryReview
from jalada.modules.ledger.application.match_review import MatchReview
from jalada.modules.ledger.application.suggesting import suggest_same_purchase
from jalada.modules.ledger.domain.audit import AuditAction
from jalada.modules.ledger.domain.entries import Correction
from jalada.modules.ledger.domain.suggestions import SuggestionStatus
from jalada.modules.ledger.domain.transactions import Transaction, TransactionStatus
from jalada.shared.errors import SuggestionNotFound


@pytest.fixture
def matches(store: Store, clock: FixedClock) -> MatchReview:
    return MatchReview(lambda: FakeUnitOfWork(store), clock)


@pytest.fixture
def joined(send: Send, store: Store, matches: MatchReview) -> tuple[uuid.UUID, Transaction]:
    """A receipt and its payment, joined by a yes. Returns the suggestion and the payment
    as it was before the yes."""
    send("receipt")
    send("message")
    [suggestion] = store.suggestions.values()
    before = store.transactions[suggestion.payment_id]
    matches.accept(USER, suggestion.id)
    return suggestion.id, before


def test_undo_puts_both_back_as_they_were(
    joined: tuple[uuid.UUID, Transaction], store: Store, matches: MatchReview
) -> None:
    suggestion_id, before = joined
    suggestion = store.suggestions[suggestion_id]

    matches.undo(USER, suggestion_id)

    payment = store.transactions[suggestion.payment_id]
    assert payment.evidence == before.evidence
    assert payment.lines == before.lines, "the receipt's category goes with it"
    candidate = store.transactions[suggestion.candidate_id]
    assert candidate.status == TransactionStatus.CANDIDATE
    receipt_id = candidate.evidence[0].evidence_id
    assert store.evidence[receipt_id].status == EvidenceStatus.CANDIDATE
    assert store.suggestions[suggestion_id].status == SuggestionStatus.DECLINED
    unlinked = [e.subject_id for e in store.audit_events if e.action == AuditAction.UNLINKED]
    assert unlinked == [payment.id, candidate.id]


def test_the_pair_is_not_offered_again(
    joined: tuple[uuid.UUID, Transaction], store: Store, matches: MatchReview
) -> None:
    suggestion_id, _ = joined
    matches.undo(USER, suggestion_id)

    candidate = store.transactions[store.suggestions[suggestion_id].candidate_id]
    with FakeUnitOfWork(store) as work:
        assert suggest_same_purchase(work, candidate, FixedClock().now()) == []


def test_a_category_the_user_chose_after_the_yes_stays(
    joined: tuple[uuid.UUID, Transaction],
    store: Store,
    matches: MatchReview,
    review: EntryReview,
) -> None:
    suggestion_id, _ = joined
    payment_id = store.suggestions[suggestion_id].payment_id
    review.confirm(USER, payment_id, Correction(category="personal_food"))

    matches.undo(USER, suggestion_id)

    payment = store.transactions[payment_id]
    assert payment.status == TransactionStatus.CONFIRMED
    assert payment.lines[0].category == "personal_food"
    assert len(payment.evidence) == 1


def test_questions_closed_by_the_yes_are_asked_again(
    send: Send, store: Store, matches: MatchReview
) -> None:
    send("receipt")
    send("receipt", {**RECEIPT, "counterparty": "ANOTHER SHOP"})
    send("message")
    first, second = store.suggestions.values()
    matches.accept(USER, first.id)

    matches.undo(USER, first.id)

    assert store.suggestions[second.id].status == SuggestionStatus.OPEN


def test_only_a_yes_can_be_undone_and_only_once(
    joined: tuple[uuid.UUID, Transaction], matches: MatchReview
) -> None:
    suggestion_id, _ = joined
    with pytest.raises(SuggestionNotFound):
        matches.undo(uuid.uuid4(), suggestion_id)
    matches.undo(USER, suggestion_id)
    with pytest.raises(SuggestionNotFound):
        matches.undo(USER, suggestion_id)


def test_to_check_shows_the_linked_receipt_until_it_is_taken_back(
    joined: tuple[uuid.UUID, Transaction], matches: MatchReview, review: EntryReview
) -> None:
    suggestion_id, _ = joined
    [item] = review.queue(USER)
    assert item.linked_receipt is not None
    assert item.linked_receipt.suggestion.id == suggestion_id
    assert item.linked_receipt.candidate.counterparty == "SAMPLE MUSIC SHOP"

    matches.undo(USER, suggestion_id)

    assert all(item.linked_receipt is None for item in review.queue(USER))
