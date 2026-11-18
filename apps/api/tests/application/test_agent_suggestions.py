"""The assistant's suggestions are checked and kept, and never change the ledger themselves."""

import uuid
from dataclasses import replace
from datetime import date
from typing import Any

import pytest
from fakes import FakeEvidenceStore, FakeTextReader, FakeUnitOfWork, FixedClock, Store
from receipts import USER
from samples import MPESA_SENT, confirmed_entry

from jalada.modules.agent.application.proposals import ActionProposals
from jalada.modules.agent.application.suggestions import SuggestCategory, SuggestConfirm
from jalada.modules.agent.application.tools import Tool, ToolContext
from jalada.modules.agent.domain.conversation import Thread
from jalada.modules.agent.domain.proposals import ActionKind, ActionStatus
from jalada.modules.evidence.application.evidence_capture import EvidenceCapture
from jalada.modules.evidence.domain.evidence import EvidenceSource
from jalada.modules.ledger.application.entry_review import EntryReview
from jalada.modules.ledger.application.ledger import Ledger
from jalada.modules.ledger.domain.categories import Purpose
from jalada.modules.ledger.domain.transactions import TransactionStatus
from jalada.modules.pipeline.application.evidence_processing import EvidenceProcessor
from jalada.modules.pipeline.domain.classifier import Preference
from jalada.modules.pipeline.domain.run_types import Budget

RUN = uuid.uuid4()
THREAD = uuid.uuid4()


@pytest.fixture
def proposals(store: Store, clock: FixedClock) -> ActionProposals:
    store.agent_threads[THREAD] = Thread(THREAD, USER, "Rent", clock.now(), clock.now())
    return ActionProposals(lambda: FakeUnitOfWork(store), clock)


def call(tool: Tool[Any], user: uuid.UUID = USER, **arguments: Any) -> dict[str, Any]:
    return tool.call(ToolContext(user, date(2026, 11, 18), RUN, THREAD), arguments)


def paste(
    store: Store,
    capture: EvidenceCapture,
    evidence_store: FakeEvidenceStore,
    clock: FixedClock,
    known: bool,
) -> uuid.UUID:
    if known:
        store.preferences[USER] = {
            "jane wanjiku": Preference("personal_family_support", Purpose.PERSONAL, 3)
        }
    evidence = capture.capture_text(USER, MPESA_SENT, EvidenceSource.WEB_PASTE).evidence
    EvidenceProcessor(
        lambda: FakeUnitOfWork(store), evidence_store, FakeTextReader(), clock, Budget()
    ).process(USER, evidence.id)
    [payment] = store.transactions.values()
    return payment.id


def test_confirming_a_ready_payment_is_suggested_and_nothing_changes(
    store: Store,
    capture: EvidenceCapture,
    evidence_store: FakeEvidenceStore,
    clock: FixedClock,
    review: EntryReview,
    proposals: ActionProposals,
) -> None:
    payment = paste(store, capture, evidence_store, clock, known=True)

    result = call(SuggestConfirm(review, proposals), id=str(payment))

    assert result["suggested"] == "Confirm Ksh 150.00 to JANE WANJIKU on 5 Nov 2026"
    [action] = store.agent_actions.values()
    assert (action.kind, action.status, action.run_id) == (
        ActionKind.CONFIRM_PAYMENT,
        ActionStatus.PROPOSED,
        RUN,
    )
    assert action.payload == {"entry_id": str(payment)}
    assert store.transactions[payment].status != TransactionStatus.CONFIRMED


def test_a_payment_that_is_not_ready_is_not_suggested(
    store: Store,
    capture: EvidenceCapture,
    evidence_store: FakeEvidenceStore,
    clock: FixedClock,
    review: EntryReview,
    proposals: ActionProposals,
) -> None:
    payment = paste(store, capture, evidence_store, clock, known=False)

    result = call(SuggestConfirm(review, proposals), id=str(payment))

    assert "needs details checked" in result["error"]
    assert store.agent_actions == {}


def test_another_persons_payment_cannot_be_suggested(
    store: Store,
    capture: EvidenceCapture,
    evidence_store: FakeEvidenceStore,
    clock: FixedClock,
    review: EntryReview,
    proposals: ActionProposals,
) -> None:
    payment = paste(store, capture, evidence_store, clock, known=True)

    result = call(SuggestConfirm(review, proposals), uuid.uuid4(), id=str(payment))

    assert result == {"error": "That payment is not waiting on To check."}
    assert store.agent_actions == {}


def test_a_new_category_is_suggested_with_both_names(
    store: Store, proposals: ActionProposals
) -> None:
    entry = replace(
        confirmed_entry(USER, date(2026, 7, 4), 250_000, "out", "business_other"),
        counterparty="KPLC PREPAID",
    )
    store.save_entries(entry)

    result = call(
        SuggestCategory(Ledger(lambda: FakeUnitOfWork(store)), proposals),
        id=str(entry.id),
        category="business_rent",
    )

    assert result["suggested"] == (
        "Move Ksh 2,500.00 to KPLC PREPAID on 4 Jul 2026 from Other business cost to Workspace rent"
    )
    [action] = store.agent_actions.values()
    assert action.payload == {"entry_id": str(entry.id), "category": "business_rent"}
    assert store.transactions[entry.id].lines[0].category == "business_other"


@pytest.mark.parametrize(
    ("category", "problem"),
    [
        ("salary", "not a category for this payment"),
        ("nonsense", "not a category for this payment"),
        ("business_other", "already in Other business cost"),
    ],
)
def test_a_category_that_does_not_fit_is_not_suggested(
    store: Store, proposals: ActionProposals, category: str, problem: str
) -> None:
    entry = confirmed_entry(USER, date(2026, 7, 4), 250_000, "out", "business_other")
    store.save_entries(entry)

    result = call(
        SuggestCategory(Ledger(lambda: FakeUnitOfWork(store)), proposals),
        id=str(entry.id),
        category=category,
    )

    assert problem in result["error"]
    assert store.agent_actions == {}
