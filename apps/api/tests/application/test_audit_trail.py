"""Every change to a payment or a certificate leaves one event in the audit trail."""

import uuid
from dataclasses import replace
from datetime import date

import pytest
from fakes import FakeEvidenceStore, FakeTextReader, FakeUnitOfWork, FixedClock, Store
from samples import CERTIFICATE, JPEG, MPESA_SENT, PDF

from jalada.modules.evidence.application.evidence_capture import EvidenceCapture
from jalada.modules.evidence.domain.evidence import EvidenceSource, EvidenceStatus
from jalada.modules.ledger.application.entry_review import EntryReview
from jalada.modules.ledger.domain.audit import Actor, AuditAction, SubjectType
from jalada.modules.ledger.domain.categories import Direction
from jalada.modules.ledger.domain.entries import Correction, Entry
from jalada.modules.pipeline.application.evidence_processing import EvidenceProcessor
from jalada.modules.pipeline.domain.run_types import Budget

USER = uuid.uuid4()


@pytest.fixture
def processor(
    store: Store, evidence_store: FakeEvidenceStore, clock: FixedClock
) -> EvidenceProcessor:
    reader = FakeTextReader(pdf_text=CERTIFICATE)
    return EvidenceProcessor(lambda: FakeUnitOfWork(store), evidence_store, reader, clock, Budget())


@pytest.fixture
def payment(capture: EvidenceCapture, processor: EvidenceProcessor, store: Store) -> Entry:
    evidence = capture.capture_text(USER, MPESA_SENT, EvidenceSource.WEB_PASTE).evidence
    processor.process(USER, evidence.id)
    [entry] = store.payments()
    return entry


def actions(store: Store, subject_id: uuid.UUID) -> list[tuple[Actor, AuditAction]]:
    return [(e.actor, e.action) for e in store.audit_events if e.subject_id == subject_id]


def test_the_pipeline_records_what_it_proposed(store: Store, payment: Entry) -> None:
    [proposed] = store.audit_events

    assert (proposed.subject_type, proposed.subject_id) == (SubjectType.TRANSACTION, payment.id)
    assert (proposed.actor, proposed.action) == (Actor.PIPELINE, AuditAction.PROPOSED)
    assert proposed.before is None
    assert proposed.after is not None and proposed.after["payment_code"] == payment.mpesa_code


def test_a_correction_keeps_the_payment_before_and_after(
    review: EntryReview, store: Store, payment: Entry
) -> None:
    review.confirm(USER, payment.id, Correction(amount_cents=16000, category="personal_food"))

    corrected = store.audit_events[-1]
    assert (corrected.actor, corrected.action) == (Actor.USER, AuditAction.CORRECTED)
    assert corrected.before is not None and corrected.after is not None
    assert corrected.before["amount_cents"] == payment.amount_cents
    assert corrected.after["amount_cents"] == 16000
    assert corrected.after["status"] == "confirmed"


def test_confirming_as_proposed_is_a_confirmation(
    review: EntryReview, store: Store, payment: Entry
) -> None:
    review.confirm(USER, payment.id, Correction(category="personal_food"))
    review.confirm(USER, payment.id)

    assert actions(store, payment.id) == [
        (Actor.PIPELINE, AuditAction.PROPOSED),
        (Actor.USER, AuditAction.CORRECTED),
    ], "confirming something already confirmed changes nothing and records nothing"


def test_not_a_transaction_is_recorded(review: EntryReview, store: Store, payment: Entry) -> None:
    review.mark_not_a_transaction(USER, payment.evidence_id)

    assert actions(store, payment.id)[-1] == (Actor.USER, AuditAction.REJECTED)


def test_typing_in_by_hand_is_recorded(
    review: EntryReview, capture: EvidenceCapture, store: Store
) -> None:
    evidence = capture.capture_file(USER, JPEG, EvidenceSource.WEB_UPLOAD).evidence
    store.evidence[evidence.id] = replace(
        store.evidence[evidence.id], status=EvidenceStatus.NEEDS_REVIEW
    )

    entry = review.enter_by_hand(
        USER,
        evidence.id,
        Correction(date(2026, 11, 4), 25000, Direction.OUT, "SAMPLE SHOP", "business_stock"),
    )

    [entered] = store.audit_events
    assert (entered.subject_id, entered.action, entered.before) == (
        entry.id,
        AuditAction.ENTERED,
        None,
    )


def test_certificates_are_recorded_as_entries(
    capture: EvidenceCapture, processor: EvidenceProcessor, store: Store
) -> None:
    evidence = capture.capture_file(USER, PDF, EvidenceSource.WEB_UPLOAD).evidence
    processor.process(USER, evidence.id)

    [proposed] = store.audit_events
    [certificate] = store.entries.values()
    assert (proposed.subject_type, proposed.subject_id) == (SubjectType.ENTRY, certificate.id)
    assert proposed.after is not None and proposed.after["certificate_serial"]
