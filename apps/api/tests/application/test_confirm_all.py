"""Payments that need nothing from the user are marked ready, and only those can be
confirmed together with Confirm all (design 03, "Confirming cheaply")."""

import uuid

import pytest
from fakes import FakeEvidenceStore, FakeTextReader, FakeUnitOfWork, FixedClock, Store
from receipts import USER, Send
from samples import MPESA_SENT

from jalada.modules.evidence.application.evidence_capture import EvidenceCapture
from jalada.modules.evidence.domain.evidence import EvidenceSource
from jalada.modules.ledger.application.entry_review import EntryReview
from jalada.modules.ledger.domain.categories import Purpose
from jalada.modules.pipeline.application.evidence_processing import EvidenceProcessor
from jalada.modules.pipeline.domain.classifier import Preference
from jalada.modules.pipeline.domain.run_types import Budget

# Jane was paid before, so a rule knows the category and the payment arrives ready.
KNOWN = {"jane wanjiku": Preference("personal_family_support", Purpose.PERSONAL, 3)}
SECOND = MPESA_SENT.replace("UK5AB1CD23", "UK5AB1CD29").replace("Ksh150.00", "Ksh300.00")


@pytest.fixture
def paid(
    store: Store, capture: EvidenceCapture, evidence_store: FakeEvidenceStore, clock: FixedClock
) -> Send:
    """Pastes an M-Pesa message and reads it. Returns the payment's id and the outcome."""
    store.preferences[USER] = dict(KNOWN)

    def sent(message: str = MPESA_SENT) -> tuple[uuid.UUID, str]:
        evidence = capture.capture_text(USER, message, EvidenceSource.WEB_PASTE).evidence
        processor = EvidenceProcessor(
            lambda: FakeUnitOfWork(store), evidence_store, FakeTextReader(), clock, Budget()
        )
        outcome = processor.process(USER, evidence.id)
        [payment] = [
            t for t in store.transactions.values() if t.evidence[0].evidence_id == evidence.id
        ]
        return payment.id, outcome

    return sent


def test_a_payment_with_a_known_category_is_ready(paid: Send, review: EntryReview) -> None:
    payment_id, outcome = paid()

    [item] = review.queue(USER)
    assert outcome == "proposed"
    assert item.entry is not None and item.entry.id == payment_id
    assert item.ready


def test_a_payment_with_a_question_is_not_ready(send: Send, review: EntryReview) -> None:
    send("receipt")
    send("message")

    [item] = review.queue(USER)
    assert item.match is not None
    assert not item.ready


def test_a_payment_with_no_category_is_not_ready(send: Send, review: EntryReview) -> None:
    send("message")

    [item] = review.queue(USER)
    assert item.entry is not None and item.entry.category is None
    assert not item.ready
