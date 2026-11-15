"""Taking back "Not a transaction" when it was chosen by mistake."""

import uuid
from dataclasses import replace
from datetime import date

import pytest
from fakes import FakeEvidenceStore, FakeTextReader, FakeUnitOfWork, FixedClock, Store
from receipts import USER, Send
from samples import JPEG, MPESA_SENT, PDF, certificate

from jalada.modules.evidence.application.evidence_capture import EvidenceCapture
from jalada.modules.evidence.domain.evidence import EvidenceSource, EvidenceStatus
from jalada.modules.ledger.application.entry_review import EntryReview
from jalada.modules.ledger.domain.audit import AuditAction
from jalada.modules.ledger.domain.entries import EntryStatus
from jalada.modules.ledger.domain.transactions import TransactionStatus
from jalada.modules.pipeline.application.evidence_processing import EvidenceProcessor
from jalada.modules.pipeline.domain.run_types import Budget
from jalada.shared.errors import EvidenceNotFound, InvalidEntry


@pytest.fixture
def message(
    capture: EvidenceCapture, store: Store, evidence_store: FakeEvidenceStore, clock: FixedClock
) -> uuid.UUID:
    """An M-Pesa payment waiting for a look, read by the pipeline."""
    evidence = capture.capture_text(USER, MPESA_SENT, EvidenceSource.WEB_PASTE).evidence
    EvidenceProcessor(
        lambda: FakeUnitOfWork(store), evidence_store, FakeTextReader(), clock, Budget()
    ).process(USER, evidence.id)
    return evidence.id


def test_a_payment_goes_back_to_how_it_was(
    message: uuid.UUID, store: Store, review: EntryReview
) -> None:
    [payment] = store.transactions.values()
    before = payment.status
    review.mark_not_a_transaction(USER, message)

    review.put_back(USER, message)

    assert store.transactions[payment.id].status == before
    assert store.evidence[message].status == EvidenceStatus.NEEDS_REVIEW
    assert store.audit_events[-1].action == AuditAction.RESTORED
    [item] = review.queue(USER)
    assert item.entry is not None and item.entry.id == payment.id


def test_a_receipt_goes_back_to_waiting_for_its_payment(
    send: Send, store: Store, review: EntryReview
) -> None:
    receipt_id, _ = send("receipt")
    review.mark_not_a_transaction(USER, receipt_id)

    review.put_back(USER, receipt_id)

    [candidate] = store.transactions.values()
    assert candidate.status == TransactionStatus.CANDIDATE
    assert store.evidence[receipt_id].status == EvidenceStatus.CANDIDATE


def test_a_certificate_goes_back_to_how_it_was(
    capture: EvidenceCapture, store: Store, review: EntryReview
) -> None:
    evidence = capture.capture_file(USER, PDF, EvidenceSource.WEB_UPLOAD).evidence
    waiting = replace(
        certificate(USER, date(2026, 3, 3), 4_000_000, 200_000, "SAMPLE CLIENT LTD"),
        evidence_id=evidence.id,
        status=EntryStatus.PROPOSED,
    )
    store.entries[waiting.id] = waiting
    review.mark_not_a_transaction(USER, evidence.id)

    review.put_back(USER, evidence.id)

    assert store.entries[waiting.id].status == EntryStatus.PROPOSED
    assert store.evidence[evidence.id].status == EvidenceStatus.PROPOSED


def test_evidence_nothing_could_read_waits_to_be_typed_in_again(
    capture: EvidenceCapture, store: Store, review: EntryReview
) -> None:
    evidence = capture.capture_file(USER, JPEG, EvidenceSource.WEB_UPLOAD).evidence
    store.evidence[evidence.id] = replace(store.evidence[evidence.id], status=EvidenceStatus.FAILED)
    review.mark_not_a_transaction(USER, evidence.id)

    review.put_back(USER, evidence.id)

    [item] = review.queue(USER)
    assert item.evidence.id == evidence.id and item.entry is None


def test_only_evidence_marked_not_a_transaction_can_be_put_back(
    message: uuid.UUID, review: EntryReview
) -> None:
    with pytest.raises(InvalidEntry):
        review.put_back(USER, message)


def test_only_my_own_evidence_can_be_put_back(message: uuid.UUID, review: EntryReview) -> None:
    review.mark_not_a_transaction(USER, message)

    with pytest.raises(EvidenceNotFound):
        review.put_back(uuid.uuid4(), message)
