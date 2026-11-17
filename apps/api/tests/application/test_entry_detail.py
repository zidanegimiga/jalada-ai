import uuid

import pytest
from fakes import FakeEvidenceStore, FakeTextReader, FakeUnitOfWork, FixedClock, Store
from samples import MPESA_SENT

from jalada.modules.evidence.application.evidence_capture import EvidenceCapture
from jalada.modules.evidence.domain.evidence import EvidenceSource
from jalada.modules.ledger.application.entry_review import EntryReview
from jalada.modules.ledger.application.ledger import Ledger
from jalada.modules.ledger.domain.audit import Actor, AuditAction
from jalada.modules.ledger.domain.entries import Correction, Entry
from jalada.modules.ledger.domain.transactions import EvidenceRole
from jalada.modules.pipeline.application.evidence_processing import EvidenceProcessor
from jalada.modules.pipeline.domain.run_types import Budget
from jalada.shared.errors import EntryNotFound

USER = uuid.uuid4()


@pytest.fixture
def corrected(
    capture: EvidenceCapture,
    review: EntryReview,
    store: Store,
    evidence_store: FakeEvidenceStore,
    clock: FixedClock,
) -> Entry:
    """A pasted M-Pesa payment, read by the pipeline, then confirmed with a new amount."""
    processor = EvidenceProcessor(
        lambda: FakeUnitOfWork(store), evidence_store, FakeTextReader(), clock, Budget()
    )
    evidence = capture.capture_text(USER, MPESA_SENT, EvidenceSource.WEB_PASTE).evidence
    processor.process(USER, evidence.id)
    [entry] = store.payments()
    return review.confirm(
        USER, entry.id, Correction(category="personal_family_support", amount_cents=16000)
    )


@pytest.fixture
def ledger(store: Store) -> Ledger:
    return Ledger(lambda: FakeUnitOfWork(store))


def test_the_detail_holds_the_payment_its_message_and_its_history(
    ledger: Ledger, corrected: Entry
) -> None:
    detail = ledger.detail(USER, corrected.id)

    assert detail.entry == corrected
    [message] = detail.evidence
    assert message.evidence_id == corrected.evidence_id
    assert message.role == EvidenceRole.PAYMENT_PROOF
    assert message.content_type.startswith("text/")
    read, confirmed = detail.history
    assert (read.actor, read.action, read.changed) == (Actor.PIPELINE, AuditAction.PROPOSED, ())
    assert (confirmed.actor, confirmed.action) == (Actor.USER, AuditAction.CORRECTED)
    assert set(confirmed.changed) == {"amount", "category"}


def test_another_users_payment_is_not_found(ledger: Ledger, corrected: Entry) -> None:
    with pytest.raises(EntryNotFound):
        ledger.detail(uuid.uuid4(), corrected.id)
