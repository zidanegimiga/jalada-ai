"""The pipeline proposes payments as transactions, and certificates as entries."""

import uuid
from dataclasses import replace
from datetime import UTC, date, datetime

import pytest
from fakes import FakeEvidenceStore, FakeTextReader, FakeUnitOfWork, FixedClock, Store
from samples import CERTIFICATE, JPEG, MPESA_SENT, PDF

from jalada.modules.evidence.application.evidence_capture import EvidenceCapture
from jalada.modules.evidence.domain.evidence import EvidenceKind, EvidenceSource, EvidenceStatus
from jalada.modules.ledger.application.entry_review import EntryReview
from jalada.modules.ledger.domain.categories import Direction
from jalada.modules.ledger.domain.entries import Correction
from jalada.modules.ledger.domain.money_accounts import MoneyAccountKind, default_accounts
from jalada.modules.ledger.domain.transactions import EvidenceRole, LinkedBy, TransactionStatus
from jalada.modules.pipeline.application.evidence_processing import EvidenceProcessor
from jalada.modules.pipeline.domain.run_types import Budget

USER = uuid.uuid4()
NOW = datetime(2026, 11, 14, 9, 0, tzinfo=UTC)


@pytest.fixture
def mpesa(store: Store) -> uuid.UUID:
    for account in default_accounts(USER, NOW):
        store.money_accounts[account.id] = account
    return next(a.id for a in store.money_accounts.values() if a.kind == MoneyAccountKind.MPESA)


@pytest.fixture
def processor(
    store: Store, evidence_store: FakeEvidenceStore, clock: FixedClock
) -> EvidenceProcessor:
    reader = FakeTextReader(pdf_text=CERTIFICATE)
    return EvidenceProcessor(lambda: FakeUnitOfWork(store), evidence_store, reader, clock, Budget())


def test_an_mpesa_message_becomes_a_payment_on_the_mpesa_account(
    store: Store, capture: EvidenceCapture, processor: EvidenceProcessor, mpesa: uuid.UUID
) -> None:
    evidence = capture.capture_text(USER, MPESA_SENT, EvidenceSource.WEB_PASTE).evidence

    processor.process(USER, evidence.id)

    [payment] = store.transactions.values()
    assert payment.account_id == mpesa
    assert payment.status == TransactionStatus.NEEDS_REVIEW
    assert (
        payment.payment_code is not None and payment.amount_cents == payment.lines[0].amount_cents
    )
    [link] = payment.evidence
    assert (link.evidence_id, link.role, link.linked_by) == (
        evidence.id,
        EvidenceRole.PAYMENT_PROOF,
        LinkedBy.PIPELINE,
    )
    assert store.entries == {}, "payments are not entries any more"


def test_a_certificate_stays_an_entry(
    store: Store, capture: EvidenceCapture, processor: EvidenceProcessor, mpesa: uuid.UUID
) -> None:
    evidence = capture.capture_file(USER, PDF, EvidenceSource.WEB_UPLOAD).evidence

    processor.process(USER, evidence.id)

    assert len(store.entries) == 1
    assert store.transactions == {}


def test_a_photo_typed_in_by_hand_is_a_receipt_with_no_account_yet(
    store: Store, capture: EvidenceCapture, review: EntryReview, mpesa: uuid.UUID
) -> None:
    evidence = capture.capture_file(USER, JPEG, EvidenceSource.WEB_UPLOAD).evidence
    store.evidence[evidence.id] = replace(
        store.evidence[evidence.id], kind=EvidenceKind.RECEIPT, status=EvidenceStatus.NEEDS_REVIEW
    )

    entry = review.enter_by_hand(
        USER,
        evidence.id,
        Correction(date(2026, 11, 4), 25000, Direction.OUT, "SAMPLE SHOP", "business_stock"),
    )

    payment = store.transactions[entry.id]
    assert payment.account_id is None
    assert payment.status == TransactionStatus.CONFIRMED
    [link] = payment.evidence
    assert (link.role, link.linked_by) == (EvidenceRole.RECEIPT, LinkedBy.USER)
    assert review.queue(USER) == []
