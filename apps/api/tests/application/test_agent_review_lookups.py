import uuid
from datetime import date
from typing import Any

from fakes import FakeEvidenceStore, FakeTextReader, FakeUnitOfWork, FixedClock, Store
from samples import MPESA_PAYBILL, MPESA_SENT

from jalada.modules.agent.application.lookups.review import PaymentDetails, WaitingToCheck
from jalada.modules.agent.application.tools import Tool, ToolContext
from jalada.modules.evidence.application.evidence_capture import EvidenceCapture
from jalada.modules.evidence.domain.evidence import EvidenceSource
from jalada.modules.ledger.application.entry_review import EntryReview
from jalada.modules.ledger.application.ledger import Ledger
from jalada.modules.ledger.domain.entries import Correction
from jalada.modules.pipeline.application.evidence_processing import EvidenceProcessor
from jalada.modules.pipeline.domain.run_types import Budget

ME, SOMEONE_ELSE = uuid.uuid4(), uuid.uuid4()


def paste(
    user: uuid.UUID,
    text: str,
    capture: EvidenceCapture,
    store: Store,
    evidence_store: FakeEvidenceStore,
    clock: FixedClock,
) -> None:
    processor = EvidenceProcessor(
        lambda: FakeUnitOfWork(store), evidence_store, FakeTextReader(), clock, Budget()
    )
    evidence = capture.capture_text(user, text, EvidenceSource.WEB_PASTE).evidence
    processor.process(user, evidence.id)


def call(tool: Tool[Any], user: uuid.UUID = ME, **arguments: Any) -> dict[str, Any]:
    return tool.call(ToolContext(user, date(2026, 11, 18)), arguments)


def test_waiting_to_check_lists_what_is_waiting_and_why(
    capture: EvidenceCapture,
    review: EntryReview,
    store: Store,
    evidence_store: FakeEvidenceStore,
    clock: FixedClock,
) -> None:
    paste(ME, MPESA_SENT, capture, store, evidence_store, clock)
    paste(SOMEONE_ELSE, MPESA_PAYBILL, capture, store, evidence_store, clock)

    waiting = call(WaitingToCheck(review))

    assert (waiting["waiting"], waiting["at_least"]) == (1, False)
    [item] = waiting["first"]
    assert (item["amount"], item["evidence"], item["direction"]) == (
        "150.00",
        "mpesa_message",
        "out",
    )
    assert item["why"]
    assert "419.00" not in str(waiting)


def test_payment_details_show_evidence_and_changes_but_not_the_message(
    capture: EvidenceCapture,
    review: EntryReview,
    store: Store,
    evidence_store: FakeEvidenceStore,
    clock: FixedClock,
) -> None:
    paste(ME, MPESA_SENT, capture, store, evidence_store, clock)
    [entry] = store.payments()
    review.confirm(ME, entry.id, Correction(category="personal_family_support", amount_cents=16000))
    ledger = Ledger(lambda: FakeUnitOfWork(store))

    detail = call(PaymentDetails(ledger), id=str(entry.id))

    assert (detail["amount"], detail["category_name"]) == ("160.00", "Family support given")
    assert detail["evidence"][0]["role"] == "payment_proof"
    assert detail["history"][-1] == {
        "date": detail["history"][-1]["date"],
        "by": "user",
        "action": "corrected",
        "changed": ["amount", "category"],
    }
    assert "balance" not in str(detail).lower()


def test_another_persons_payment_is_not_found(
    capture: EvidenceCapture,
    store: Store,
    evidence_store: FakeEvidenceStore,
    clock: FixedClock,
) -> None:
    paste(SOMEONE_ELSE, MPESA_SENT, capture, store, evidence_store, clock)
    [theirs] = store.payments()

    found = call(PaymentDetails(Ledger(lambda: FakeUnitOfWork(store))), id=str(theirs.id))

    assert found == {"error": "There is no payment with that id."}
