"""A receipt waits as a candidate, and is offered to the user as the same purchase as a
payment that fits it, whichever arrives first (design 03, "Candidates")."""

import pytest
from fakes import Store
from receipts import RECEIPT, USER, Send

from jalada.modules.evidence.domain.evidence import EvidenceStatus
from jalada.modules.ledger.application.entry_review import EntryReview
from jalada.modules.ledger.domain.suggestions import SuggestionKind, SuggestionStatus
from jalada.modules.ledger.domain.transactions import TransactionStatus


def test_a_receipt_waits_as_a_candidate_and_is_not_on_to_check(
    send: Send, store: Store, review: EntryReview
) -> None:
    evidence_id, outcome = send("receipt")

    assert outcome == "candidate"
    [candidate] = store.transactions.values()
    assert candidate.status == TransactionStatus.CANDIDATE
    assert candidate.account_id is None, "how it was paid is not known"
    assert store.evidence[evidence_id].status == EvidenceStatus.CANDIDATE
    assert review.queue(USER) == []
    assert store.suggestions == {}


def test_a_receipt_with_no_amount_goes_straight_to_the_user(
    send: Send, store: Store, review: EntryReview
) -> None:
    evidence_id, outcome = send("receipt", {**RECEIPT, "amount_ksh": None})

    assert outcome == "needs_review"
    assert [t.status for t in store.transactions.values()] != [TransactionStatus.CANDIDATE]
    assert [item.evidence.id for item in review.queue(USER)] == [evidence_id]


@pytest.mark.parametrize("order", [("receipt", "message"), ("message", "receipt")])
def test_a_receipt_and_its_payment_are_offered_as_one_purchase(
    send: Send, store: Store, order: tuple[str, str]
) -> None:
    for what in order:
        send(what)

    [suggestion] = store.suggestions.values()
    [candidate] = [t for t in store.transactions.values() if t.status == "candidate"]
    [payment] = [t for t in store.transactions.values() if t.status != "candidate"]
    assert (suggestion.candidate_id, suggestion.payment_id) == (candidate.id, payment.id)
    assert suggestion.kind == SuggestionKind.SAME_PURCHASE
    assert suggestion.status == SuggestionStatus.OPEN
    assert suggestion.reasons == ("same amount", "same day")
    assert payment.evidence[1:] == (), "nothing is linked until the user says so"


def test_a_receipt_for_another_amount_is_not_offered(send: Send, store: Store) -> None:
    send("message")
    send("receipt", {**RECEIPT, "amount_ksh": "420.00"})

    assert store.suggestions == {}
