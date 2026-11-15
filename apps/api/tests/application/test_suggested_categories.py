"""A model's category is a suggestion until the user accepts or changes it (design 03)."""

import uuid

import pytest
from fakes import (
    FakeEvidenceStore,
    FakeTextReader,
    FakeUnitOfWork,
    FixedClock,
    ScriptedModel,
    Store,
)
from samples import JPEG

from jalada.modules.evidence.application.evidence_capture import EvidenceCapture
from jalada.modules.evidence.domain.evidence import EvidenceSource
from jalada.modules.ledger.application.entry_review import EntryReview
from jalada.modules.ledger.domain.entries import Correction
from jalada.modules.pipeline.application.evidence_processing import EvidenceProcessor
from jalada.modules.pipeline.domain.run_types import Budget

USER = uuid.uuid4()
RECEIPT = {
    "kind": "receipt",
    "occurred_on": "2026-11-04",
    "direction": "out",
    "amount_ksh": "250.00",
    "counterparty": "SAMPLE SHOP",
    "confidence": 0.95,
}
STOCK = {"purpose": "business", "category": "business_stock", "confidence": 0.95}


@pytest.fixture
def suggested(
    store: Store, capture: EvidenceCapture, evidence_store: FakeEvidenceStore, clock: FixedClock
) -> uuid.UUID:
    """A receipt photo read and classified by a model, sure of itself."""
    model = ScriptedModel(RECEIPT, STOCK)
    evidence = capture.capture_file(USER, JPEG, EvidenceSource.WEB_UPLOAD).evidence
    processor = EvidenceProcessor(
        lambda: FakeUnitOfWork(store),
        evidence_store,
        FakeTextReader(),
        clock,
        Budget(),
        model=model,
    )
    assert processor.process(USER, evidence.id) == "needs_review"
    [payment] = store.transactions.values()
    return payment.id


def test_a_model_category_waits_as_a_suggestion(
    store: Store, review: EntryReview, suggested: uuid.UUID
) -> None:
    [item] = review.queue(USER)

    assert item.entry is not None and item.entry.category == "business_stock"
    assert item.category_suggested
    assert store.transactions[suggested].lines[0].suggested


def test_confirming_accepts_the_suggestion(
    store: Store, review: EntryReview, suggested: uuid.UUID
) -> None:
    review.confirm(USER, suggested)

    assert not store.transactions[suggested].lines[0].suggested


def test_changing_the_category_replaces_the_suggestion(
    store: Store, review: EntryReview, suggested: uuid.UUID
) -> None:
    review.confirm(USER, suggested, Correction(category="personal_food"))

    [line] = store.transactions[suggested].lines
    assert (line.category, line.suggested) == ("personal_food", False)


def test_a_category_from_a_past_choice_is_not_a_suggestion(
    store: Store,
    review: EntryReview,
    suggested: uuid.UUID,
    capture: EvidenceCapture,
    evidence_store: FakeEvidenceStore,
    clock: FixedClock,
) -> None:
    review.confirm(USER, suggested)  # teaches SAMPLE SHOP -> business_stock
    model = ScriptedModel(RECEIPT)
    photo = capture.capture_file(USER, JPEG + b"2", EvidenceSource.WEB_UPLOAD).evidence
    EvidenceProcessor(
        lambda: FakeUnitOfWork(store),
        evidence_store,
        FakeTextReader(),
        clock,
        Budget(),
        model=model,
    ).process(USER, photo.id)

    [item] = review.queue(USER)
    assert item.entry is not None and item.entry.category == "business_stock"
    assert not item.category_suggested
