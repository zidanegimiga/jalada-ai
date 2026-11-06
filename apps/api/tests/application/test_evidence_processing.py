import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from fakes import (
    FakeEvidenceStore,
    FakeTextReader,
    FakeUnitOfWork,
    FixedClock,
    ScriptedModel,
    Store,
)
from samples import CERTIFICATE, JPEG, MPESA_SENT, PDF

from jalada.application.evidence_capture import EvidenceCapture
from jalada.application.evidence_processing import EvidenceProcessor
from jalada.domain.categories import Purpose
from jalada.domain.entries import EntryStatus
from jalada.domain.evidence import EvidenceKind, EvidenceSource, EvidenceStatus
from jalada.pipeline.classifier import Preference
from jalada.pipeline.run_types import Budget

USER = uuid.uuid4()


@pytest.fixture
def reader() -> FakeTextReader:
    return FakeTextReader(pdf_text=CERTIFICATE)


@pytest.fixture
def processor(
    store: Store, evidence_store: FakeEvidenceStore, reader: FakeTextReader, clock: FixedClock
) -> EvidenceProcessor:
    return EvidenceProcessor(lambda: FakeUnitOfWork(store), evidence_store, reader, clock, Budget())


def test_a_message_from_a_known_counterparty_becomes_a_proposed_entry(
    capture: EvidenceCapture, processor: EvidenceProcessor, store: Store
) -> None:
    store.preferences[USER] = {
        "jane wanjiku": Preference("personal_family_support", Purpose.PERSONAL, 2)
    }
    evidence = capture.capture_text(USER, MPESA_SENT, EvidenceSource.WEB_PASTE).evidence

    assert processor.process(USER, evidence.id) == "proposed"

    [entry] = store.entries.values()
    assert entry.status == EntryStatus.PROPOSED
    assert entry.amount_cents == 15000
    assert entry.category == "personal_family_support"
    assert entry.evidence_id == evidence.id
    assert store.evidence[evidence.id].status == EvidenceStatus.PROPOSED
    assert store.evidence[evidence.id].kind == EvidenceKind.MPESA_MESSAGE
    [(run, steps)] = store.runs
    assert entry.run_id == run.id
    assert run.outcome == "proposed" and len(steps) == 4


def test_a_message_from_today_in_kenya_is_not_in_the_future_while_utc_is_still_on_yesterday(
    capture: EvidenceCapture, processor: EvidenceProcessor, store: Store, clock: FixedClock
) -> None:
    # 1 am on 5 November in Nairobi, still 4 November in UTC. The message is dated 5/11/26.
    clock.current = datetime(2026, 11, 4, 22, 0, tzinfo=UTC)
    store.preferences[USER] = {
        "jane wanjiku": Preference("personal_family_support", Purpose.PERSONAL, 2)
    }
    evidence = capture.capture_text(USER, MPESA_SENT, EvidenceSource.WEB_PASTE).evidence

    assert processor.process(USER, evidence.id) == "proposed"


def test_an_unknown_counterparty_becomes_an_entry_that_needs_review(
    capture: EvidenceCapture, processor: EvidenceProcessor, store: Store
) -> None:
    evidence = capture.capture_text(USER, MPESA_SENT, EvidenceSource.WEB_PASTE).evidence

    processor.process(USER, evidence.id)

    [entry] = store.entries.values()
    assert entry.status == EntryStatus.NEEDS_REVIEW
    assert entry.purpose == Purpose.UNSURE
    assert store.evidence[evidence.id].status == EvidenceStatus.NEEDS_REVIEW


def test_a_certificate_pdf_is_read_and_proposed(
    capture: EvidenceCapture, processor: EvidenceProcessor, store: Store
) -> None:
    evidence = capture.capture_file(USER, PDF, EvidenceSource.WEB_UPLOAD).evidence

    assert processor.process(USER, evidence.id) == "proposed"

    [entry] = store.entries.values()
    assert entry.certificate_serial == "KRAWHTEON0000000001"
    assert entry.tax_withheld_cents == 200000
    assert entry.payer_tax_number == "P000000000A"


def test_the_same_transaction_sent_twice_is_a_duplicate(
    capture: EvidenceCapture, processor: EvidenceProcessor, store: Store
) -> None:
    first = capture.capture_text(USER, MPESA_SENT, EvidenceSource.WEB_PASTE).evidence
    processor.process(USER, first.id)
    # The same transaction code with different spacing, so it is new evidence.
    second = capture.capture_text(USER, MPESA_SENT.replace("  ", " "), EvidenceSource.WEB_PASTE)

    assert processor.process(USER, second.evidence.id) == "duplicate"
    assert len(store.entries) == 1
    assert store.evidence[second.evidence.id].status == EvidenceStatus.DUPLICATE


def test_a_photo_without_text_needs_review_and_creates_no_entry(
    capture: EvidenceCapture, processor: EvidenceProcessor, store: Store
) -> None:
    evidence = capture.capture_file(USER, JPEG, EvidenceSource.WEB_UPLOAD).evidence

    assert processor.process(USER, evidence.id) == "needs_review"
    assert store.entries == {}


def test_giving_up_marks_the_evidence_as_failed(
    capture: EvidenceCapture, processor: EvidenceProcessor, store: Store
) -> None:
    evidence = capture.capture_file(USER, JPEG, EvidenceSource.WEB_UPLOAD).evidence

    processor.give_up({"user_id": str(USER), "evidence_id": str(evidence.id)})

    assert store.evidence[evidence.id].status == EvidenceStatus.FAILED


def test_a_photo_read_by_the_model_records_what_it_cost(
    capture: EvidenceCapture,
    store: Store,
    evidence_store: FakeEvidenceStore,
    reader: FakeTextReader,
    clock: FixedClock,
) -> None:
    model = ScriptedModel(
        {
            "kind": "receipt",
            "occurred_on": "2026-11-04",
            "direction": "out",
            "amount_ksh": "250.00",
            "counterparty": "SAMPLE SHOP",
            "confidence": 0.9,
        },
        {"purpose": "business", "category": "business_stock", "confidence": 0.9},
    )
    processor = EvidenceProcessor(
        lambda: FakeUnitOfWork(store), evidence_store, reader, clock, Budget(), model
    )
    evidence = capture.capture_file(USER, JPEG, EvidenceSource.WEB_UPLOAD).evidence

    assert processor.process(USER, evidence.id) == "proposed"

    [(run, _)] = store.runs
    assert (run.input_tokens, run.output_tokens) == (200, 100)
    assert run.cost_usd == Decimal("0.002")
    assert model.calls[0]["image"].data == JPEG
    assert store.evidence[evidence.id].kind == EvidenceKind.RECEIPT
