import uuid
from dataclasses import replace
from datetime import date

import pytest
from fakes import FakeEvidenceStore, FakeTextReader, FakeUnitOfWork, FixedClock, Store
from samples import JPEG, MPESA_SENT, PDF, certificate, confirmed_entry

from jalada.modules.evidence.application.evidence_capture import EvidenceCapture
from jalada.modules.evidence.domain.evidence import EvidenceSource, EvidenceStatus
from jalada.modules.ledger.application.entry_review import EntryReview
from jalada.modules.ledger.domain.audit import AuditAction
from jalada.modules.ledger.domain.categories import Direction, Purpose
from jalada.modules.ledger.domain.entries import Correction, Entry, EntryStatus
from jalada.modules.ledger.domain.transactions import (
    EvidenceRole,
    TransactionStatus,
    as_entry,
    from_entry,
)
from jalada.modules.pipeline.application.evidence_processing import EvidenceProcessor
from jalada.modules.pipeline.domain.run_types import Budget
from jalada.shared.errors import EntryNotFound, EvidenceNotFound, InvalidEntry

USER = uuid.uuid4()
OTHER = uuid.uuid4()


@pytest.fixture
def processed(
    capture: EvidenceCapture, store: Store, evidence_store: FakeEvidenceStore, clock: FixedClock
) -> Entry:
    """An M-Pesa payment to an unknown person, read by the pipeline and waiting for review."""
    processor = EvidenceProcessor(
        lambda: FakeUnitOfWork(store), evidence_store, FakeTextReader(), clock, Budget()
    )
    evidence = capture.capture_text(USER, MPESA_SENT, EvidenceSource.WEB_PASTE).evidence
    processor.process(USER, evidence.id)
    [entry] = store.payments()
    return entry


def test_the_queue_lists_entries_waiting_for_review(review: EntryReview, processed: Entry) -> None:
    [item] = review.queue(USER)

    assert item.entry == processed
    assert item.evidence.id == processed.evidence_id
    assert review.queue(OTHER) == []


def test_an_entry_without_a_category_cannot_be_confirmed_as_is(
    review: EntryReview, processed: Entry
) -> None:
    with pytest.raises(InvalidEntry, match="Add the category"):
        review.confirm(USER, processed.id)


def test_correcting_confirms_learns_and_keeps_the_history(
    review: EntryReview, processed: Entry, store: Store
) -> None:
    confirmed = review.confirm(
        USER, processed.id, Correction(category="personal_family_support", amount_cents=16000)
    )

    assert confirmed.status == EntryStatus.CONFIRMED
    assert confirmed.amount_cents == 16000
    assert confirmed.purpose == Purpose.PERSONAL
    assert confirmed.confirmed_at is not None
    assert store.evidence[processed.evidence_id].status == EvidenceStatus.CONFIRMED
    assert as_entry(store.transactions[processed.id]) == confirmed
    [_, corrected] = store.audit_events
    assert corrected.action == AuditAction.CORRECTED
    assert corrected.after is not None and corrected.after["amount_cents"] == 16000
    learned = store.preferences[USER]["jane wanjiku"]
    assert (learned.category, learned.times_used) == ("personal_family_support", 1)
    assert review.queue(USER) == []


def test_choosing_the_same_category_again_counts_for_more(
    review: EntryReview, processed: Entry, store: Store
) -> None:
    review.confirm(USER, processed.id, Correction(category="personal_food"))
    review.confirm(USER, processed.id, Correction(category="personal_food"))

    assert store.preferences[USER]["jane wanjiku"].times_used == 2

    review.confirm(USER, processed.id, Correction(category="personal_other"))

    assert store.preferences[USER]["jane wanjiku"].times_used == 1


def test_confirming_twice_without_changes_does_nothing_more(
    review: EntryReview, processed: Entry, store: Store
) -> None:
    review.confirm(USER, processed.id, Correction(category="personal_food"))

    review.confirm(USER, processed.id)

    assert [e.action for e in store.audit_events] == [
        AuditAction.PROPOSED,
        AuditAction.CORRECTED,
    ]


@pytest.mark.parametrize(
    ("correction", "message"),
    [
        (Correction(category="salary"), "does not fit"),
        (Correction(category="made_up"), "does not exist"),
        (Correction(category="personal_food", amount_cents=0), "more than zero"),
    ],
)
def test_bad_corrections_are_refused(
    review: EntryReview, processed: Entry, correction: Correction, message: str
) -> None:
    with pytest.raises(InvalidEntry, match=message):
        review.confirm(USER, processed.id, correction)


def test_nobody_else_can_confirm_my_entry(review: EntryReview, processed: Entry) -> None:
    with pytest.raises(EntryNotFound):
        review.confirm(OTHER, processed.id, Correction(category="personal_food"))


def test_unreadable_evidence_waits_for_an_entry_typed_in_by_hand(
    review: EntryReview, capture: EvidenceCapture, store: Store
) -> None:
    evidence = capture.capture_file(USER, JPEG, EvidenceSource.WEB_UPLOAD).evidence
    store.evidence[evidence.id] = replace(
        store.evidence[evidence.id], status=EvidenceStatus.NEEDS_REVIEW
    )

    [item] = review.queue(USER)
    assert item.entry is None

    entry = review.enter_by_hand(
        USER,
        evidence.id,
        Correction(date(2026, 11, 4), 25000, Direction.OUT, "SAMPLE SHOP", "business_stock"),
    )

    assert entry.status == EntryStatus.CONFIRMED
    assert entry.run_id is None
    assert entry.purpose == Purpose.BUSINESS
    assert review.queue(USER) == []
    with pytest.raises(InvalidEntry, match="already has an entry"):
        review.enter_by_hand(USER, evidence.id, Correction(category="business_stock"))


def test_typing_in_needs_the_evidence_to_be_mine(review: EntryReview) -> None:
    with pytest.raises(EvidenceNotFound):
        review.enter_by_hand(USER, uuid.uuid4(), Correction(category="personal_food"))


def test_not_a_transaction_rejects_the_payment_and_keeps_the_history(
    review: EntryReview, processed: Entry, store: Store
) -> None:
    review.mark_not_a_transaction(USER, processed.evidence_id)

    rejected = store.transactions[processed.id]
    assert rejected.status == TransactionStatus.REJECTED
    assert store.audit_events[-1].action == AuditAction.REJECTED
    assert store.evidence[processed.evidence_id].status == EvidenceStatus.NOT_A_TRANSACTION
    assert USER not in store.preferences
    assert review.queue(USER) == []


def test_unreadable_evidence_can_be_marked_not_a_transaction(
    review: EntryReview, capture: EvidenceCapture, store: Store
) -> None:
    evidence = capture.capture_file(USER, JPEG, EvidenceSource.WEB_UPLOAD).evidence
    store.evidence[evidence.id] = replace(
        store.evidence[evidence.id], status=EvidenceStatus.NEEDS_REVIEW
    )

    review.mark_not_a_transaction(USER, evidence.id)

    assert store.evidence[evidence.id].status == EvidenceStatus.NOT_A_TRANSACTION
    assert review.queue(USER) == []


def test_a_confirmed_entry_cannot_be_marked_not_a_transaction(
    review: EntryReview, processed: Entry
) -> None:
    review.confirm(USER, processed.id, Correction(category="personal_food"))

    with pytest.raises(InvalidEntry, match="already in your ledger"):
        review.mark_not_a_transaction(USER, processed.evidence_id)


def test_not_a_transaction_needs_the_evidence_to_be_mine(
    review: EntryReview, processed: Entry
) -> None:
    with pytest.raises(EvidenceNotFound):
        review.mark_not_a_transaction(OTHER, processed.evidence_id)


def test_the_queue_reads_payments_from_transactions_and_certificates_from_entries(
    review: EntryReview, capture: EvidenceCapture, store: Store
) -> None:
    message = capture.capture_text(USER, MPESA_SENT, EvidenceSource.WEB_PASTE).evidence
    payment = replace(
        confirmed_entry(USER, date(2026, 11, 4), 15000, "out", "personal_food"),
        evidence_id=message.id,
        status=EntryStatus.PROPOSED,
    )
    store.transactions[payment.id] = from_entry(payment, None, EvidenceRole.PAYMENT_PROOF)
    pdf = capture.capture_file(USER, PDF, EvidenceSource.WEB_UPLOAD).evidence
    waiting_certificate = replace(
        certificate(USER, date(2026, 3, 3), 4_000_000, 200_000, "CLIENT"),
        evidence_id=pdf.id,
        status=EntryStatus.NEEDS_REVIEW,
    )
    store.entries[waiting_certificate.id] = waiting_certificate

    shown = {item.entry.id: item.entry for item in review.queue(USER) if item.entry}

    assert shown == {payment.id: payment, waiting_certificate.id: waiting_certificate}
