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


def test_confirm_all_confirms_every_ready_payment(
    paid: Send, review: EntryReview, store: Store
) -> None:
    first, _ = paid()
    second, _ = paid(SECOND)

    confirmed = review.confirm_all(USER, [first, second])

    assert [entry.id for entry in confirmed] == [first, second]
    assert {store.transactions[t].status for t in (first, second)} == {"confirmed"}
    assert [e.action for e in store.audit_events][-2:] == ["confirmed", "confirmed"]
    assert review.queue(USER) == []


def test_only_what_was_listed_is_confirmed(paid: Send, review: EntryReview, store: Store) -> None:
    first, _ = paid()
    arrived_later, _ = paid(SECOND)

    review.confirm_all(USER, [first])

    assert store.transactions[arrived_later].status == "proposed"


def test_a_payment_that_needs_a_look_is_skipped(
    paid: Send, send: Send, review: EntryReview, store: Store
) -> None:
    ready, _ = paid()
    send("message")
    [unsure] = [t.id for t in store.transactions.values() if t.id != ready]

    confirmed = review.confirm_all(USER, [ready, unsure, uuid.uuid4()])

    assert [entry.id for entry in confirmed] == [ready]
    assert store.transactions[unsure].status == "needs_review"


def test_confirm_all_never_touches_another_users_payments(
    paid: Send, review: EntryReview, store: Store
) -> None:
    payment_id, _ = paid()

    assert review.confirm_all(uuid.uuid4(), [payment_id]) == []
    assert store.transactions[payment_id].status == "proposed"
