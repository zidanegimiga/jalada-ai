"""A receipt waits as a candidate, and is offered to the user as the same purchase as a
payment that fits it, whichever arrives first (design 03, "Candidates")."""

import uuid
from collections.abc import Callable

import pytest
from fakes import (
    FakeEvidenceStore,
    FakeTextReader,
    FakeUnitOfWork,
    FixedClock,
    ScriptedModel,
    Store,
)
from samples import JPEG, MPESA_PAYBILL

from jalada.modules.evidence.application.evidence_capture import EvidenceCapture
from jalada.modules.evidence.domain.evidence import EvidenceSource, EvidenceStatus
from jalada.modules.ledger.application.entry_review import EntryReview
from jalada.modules.ledger.domain.suggestions import SuggestionKind, SuggestionStatus
from jalada.modules.ledger.domain.transactions import TransactionStatus
from jalada.modules.pipeline.application.evidence_processing import EvidenceProcessor
from jalada.modules.pipeline.domain.run_types import Budget

USER = uuid.uuid4()
# The receipt for the paybill payment in MPESA_PAYBILL: the same amount on the same day.
RECEIPT = {
    "kind": "receipt",
    "occurred_on": "2026-11-05",
    "direction": "out",
    "amount_ksh": "419.00",
    "counterparty": "SAMPLE MUSIC SHOP",
    "confidence": 0.95,
}
LEISURE = {"purpose": "personal", "category": "personal_other", "confidence": 0.95}
Send = Callable[..., tuple[uuid.UUID, str]]


@pytest.fixture
def send(
    store: Store, capture: EvidenceCapture, evidence_store: FakeEvidenceStore, clock: FixedClock
) -> Send:
    """Sends a receipt photo ("receipt") or the paybill message ("message") and reads it."""

    def sent(what: str, receipt: dict[str, object] = RECEIPT) -> tuple[uuid.UUID, str]:
        if what == "receipt":
            photo = JPEG + uuid.uuid4().bytes
            evidence = capture.capture_file(USER, photo, EvidenceSource.WEB_UPLOAD).evidence
        else:
            evidence = capture.capture_text(USER, MPESA_PAYBILL, EvidenceSource.WEB_PASTE).evidence
        processor = EvidenceProcessor(
            lambda: FakeUnitOfWork(store),
            evidence_store,
            FakeTextReader(),
            clock,
            Budget(),
            model=ScriptedModel(receipt, LEISURE),
        )
        return evidence.id, processor.process(USER, evidence.id)

    return sent


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
