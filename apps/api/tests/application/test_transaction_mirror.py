"""While entries and transactions both exist, every write to a transaction entry also
writes its transaction."""

import uuid
from dataclasses import replace
from datetime import UTC, date, datetime

import pytest
from fakes import FakeEvidenceStore, FakeTextReader, FakeUnitOfWork, FixedClock, Store
from samples import CERTIFICATE, JPEG, MPESA_SENT, PDF, confirmed_entry

from jalada.modules.evidence.application.evidence_capture import EvidenceCapture
from jalada.modules.evidence.domain.evidence import EvidenceKind, EvidenceSource, EvidenceStatus
from jalada.modules.ledger.application.entry_review import EntryReview
from jalada.modules.ledger.application.transaction_mirror import mirror_entry
from jalada.modules.ledger.domain.categories import Direction, Purpose
from jalada.modules.ledger.domain.entries import Correction, Entry
from jalada.modules.ledger.domain.money_accounts import MoneyAccountKind, default_accounts
from jalada.modules.ledger.domain.transactions import (
    EvidenceRole,
    LinkedBy,
    TransactionLine,
    TransactionStatus,
)
from jalada.modules.pipeline.application.evidence_processing import EvidenceProcessor
from jalada.modules.pipeline.domain.run_types import Budget

USER = uuid.uuid4()
NOW = datetime(2026, 11, 14, 9, 0, tzinfo=UTC)


@pytest.fixture
def mpesa(store: Store) -> uuid.UUID:
    for account in default_accounts(USER, NOW):
        store.money_accounts[account.id] = account
    return next(a.id for a in store.money_accounts.values() if a.kind == MoneyAccountKind.MPESA)


def process(
    store: Store, capture: EvidenceCapture, evidence_store: FakeEvidenceStore, clock: FixedClock
) -> Entry:
    reader = FakeTextReader(pdf_text=CERTIFICATE)
    evidence = capture.capture_text(USER, MPESA_SENT, EvidenceSource.WEB_PASTE).evidence
    EvidenceProcessor(
        lambda: FakeUnitOfWork(store), evidence_store, reader, clock, Budget()
    ).process(USER, evidence.id)
    [entry] = store.entries.values()
    return entry


def test_a_message_read_by_the_pipeline_becomes_an_mpesa_payment(
    store: Store,
    capture: EvidenceCapture,
    evidence_store: FakeEvidenceStore,
    clock: FixedClock,
    mpesa: uuid.UUID,
) -> None:
    entry = process(store, capture, evidence_store, clock)

    transaction = store.transactions[entry.id]
    assert transaction.account_id == mpesa
    assert transaction.status == TransactionStatus(entry.status.value)
    assert (transaction.amount_cents, transaction.payment_code) == (
        entry.amount_cents,
        entry.mpesa_code,
    )
    [link] = transaction.evidence
    assert (link.evidence_id, link.role, link.linked_by) == (
        entry.evidence_id,
        EvidenceRole.PAYMENT_PROOF,
        LinkedBy.PIPELINE,
    )


def test_confirming_and_correcting_update_the_transaction(
    store: Store,
    capture: EvidenceCapture,
    evidence_store: FakeEvidenceStore,
    clock: FixedClock,
    review: EntryReview,
    mpesa: uuid.UUID,
) -> None:
    entry = process(store, capture, evidence_store, clock)

    review.confirm(USER, entry.id, Correction(amount_cents=16000, category="personal_food"))

    transaction = store.transactions[entry.id]
    assert transaction.status == TransactionStatus.CONFIRMED
    assert transaction.confirmed_at is not None
    assert transaction.lines == (TransactionLine(16000, "personal_food", Purpose.PERSONAL),)
    assert transaction.account_id == mpesa, "the account is kept"
    assert len(transaction.evidence) == 1, "the evidence link is kept"


def test_not_a_transaction_rejects_it(
    store: Store,
    capture: EvidenceCapture,
    evidence_store: FakeEvidenceStore,
    clock: FixedClock,
    review: EntryReview,
    mpesa: uuid.UUID,
) -> None:
    entry = process(store, capture, evidence_store, clock)

    review.mark_not_a_transaction(USER, entry.evidence_id)

    assert store.transactions[entry.id].status == TransactionStatus.REJECTED


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

    transaction = store.transactions[entry.id]
    assert transaction.account_id is None
    assert transaction.status == TransactionStatus.CONFIRMED
    [link] = transaction.evidence
    assert (link.role, link.linked_by) == (EvidenceRole.RECEIPT, LinkedBy.USER)


def test_certificates_get_no_transaction(
    store: Store,
    capture: EvidenceCapture,
    evidence_store: FakeEvidenceStore,
    clock: FixedClock,
    mpesa: uuid.UUID,
) -> None:
    evidence = capture.capture_file(USER, PDF, EvidenceSource.WEB_UPLOAD).evidence
    reader = FakeTextReader(pdf_text=CERTIFICATE)
    EvidenceProcessor(
        lambda: FakeUnitOfWork(store), evidence_store, reader, clock, Budget()
    ).process(USER, evidence.id)

    assert len(store.entries) == 1
    assert store.transactions == {}


def test_an_entry_from_before_transactions_gets_one_when_it_changes(
    store: Store, mpesa: uuid.UUID
) -> None:
    older = confirmed_entry(USER, date(2026, 10, 1), 5000, "out", "personal_food")

    with FakeUnitOfWork(store) as work:
        mirror_entry(work, older)
        work.commit()

    transaction = store.transactions[older.id]
    assert transaction.account_id is None, "its evidence is unknown here, so no account"
    assert transaction.evidence[0].role == EvidenceRole.OTHER
