"""The pipeline end to end against Postgres, where foreign keys and unique codes are real:
a message is proposed as a payment, a second copy is linked to it, and a receipt is offered
as the same purchase and joined into it."""

import uuid
from datetime import UTC, datetime

import pytest
from fakes import FakeEvidenceStore, FakeTextReader, FixedClock, ScriptedModel
from samples import JPEG, MPESA_PAYBILL, MPESA_SENT
from sqlalchemy.orm import Session as DbSession
from sqlalchemy.orm import sessionmaker

from jalada.modules.accounts.domain.users import User
from jalada.modules.evidence.application.evidence_capture import EvidenceCapture
from jalada.modules.evidence.domain.evidence import EvidenceSource, EvidenceStatus
from jalada.modules.ledger.application.match_review import MatchReview
from jalada.modules.ledger.domain.audit import AuditAction
from jalada.modules.ledger.domain.money_accounts import default_accounts
from jalada.modules.ledger.domain.transactions import LinkedBy, TransactionStatus
from jalada.modules.pipeline.application.evidence_processing import EvidenceProcessor
from jalada.modules.pipeline.domain.run_types import Budget
from jalada.sql_unit_of_work import SqlUnitOfWork

pytestmark = pytest.mark.integration

NOW = datetime(2026, 11, 14, 9, 0, tzinfo=UTC)


def new_user(session_factory: sessionmaker[DbSession]) -> User:
    user = User(uuid.uuid4(), f"{uuid.uuid4().hex}@example.com", "Jane", NOW)
    with SqlUnitOfWork(session_factory) as work:
        work.users.add(user, None)
        for account in default_accounts(user.id, NOW):
            work.money_accounts_for(user.id).add(account)
        work.commit()
    return user


def test_a_payment_is_proposed_and_a_second_copy_is_linked(
    session_factory: sessionmaker[DbSession],
) -> None:
    user = new_user(session_factory)
    files, clock = FakeEvidenceStore(), FixedClock()
    capture = EvidenceCapture(lambda: SqlUnitOfWork(session_factory), files, clock)
    processor = EvidenceProcessor(
        lambda: SqlUnitOfWork(session_factory), files, FakeTextReader(), clock, Budget()
    )

    first = capture.capture_text(user.id, MPESA_SENT, EvidenceSource.WEB_PASTE).evidence
    assert processor.process(user.id, first.id) == "needs_review"
    copy = MPESA_SENT.replace("  ", " ")
    second = capture.capture_text(user.id, copy, EvidenceSource.WEB_PASTE).evidence
    assert processor.process(user.id, second.id) == "linked"

    with SqlUnitOfWork(session_factory) as work:
        [payment] = work.transactions_for(user.id).pending(10)
        assert payment.status == TransactionStatus.NEEDS_REVIEW
        assert [link.linked_by for link in payment.evidence] == [LinkedBy.PIPELINE, LinkedBy.EXACT]
        linked = work.evidence_for(user.id).get(second.id)
        assert linked is not None and linked.status == EvidenceStatus.LINKED
        actions = [e.action for e in work.audit_for(user.id).for_subject(payment.id)]
        assert actions == [AuditAction.PROPOSED, AuditAction.LINKED]


def test_a_receipt_waits_and_is_offered_with_its_payment(
    session_factory: sessionmaker[DbSession],
) -> None:
    user = new_user(session_factory)
    files, clock = FakeEvidenceStore(), FixedClock()
    capture = EvidenceCapture(lambda: SqlUnitOfWork(session_factory), files, clock)
    receipt = {
        "kind": "receipt",
        "occurred_on": "2026-11-05",
        "direction": "out",
        "amount_ksh": "419.00",
        "counterparty": "SAMPLE MUSIC SHOP",
        "confidence": 0.95,
    }
    unsure = {"purpose": "unsure", "category": None, "confidence": 0.2}
    model = ScriptedModel(receipt, unsure, unsure)  # the receipt, then what each was for
    processor = EvidenceProcessor(
        lambda: SqlUnitOfWork(session_factory), files, FakeTextReader(), clock, Budget(), model
    )

    photo = capture.capture_file(user.id, JPEG, EvidenceSource.WEB_UPLOAD).evidence
    assert processor.process(user.id, photo.id) == "candidate"
    message = capture.capture_text(user.id, MPESA_PAYBILL, EvidenceSource.WEB_PASTE).evidence
    processor.process(user.id, message.id)

    with SqlUnitOfWork(session_factory) as work:
        [suggestion] = work.suggestions_for(user.id).open()
        candidate = work.transactions_for(user.id).get(suggestion.candidate_id)
        assert candidate is not None and candidate.status == TransactionStatus.CANDIDATE
        assert work.transactions_for(user.id).pending(10)[0].id == suggestion.payment_id

    MatchReview(lambda: SqlUnitOfWork(session_factory), clock).accept(user.id, suggestion.id)

    with SqlUnitOfWork(session_factory) as work:
        payment = work.transactions_for(user.id).get(suggestion.payment_id)
        assert payment is not None
        assert [link.evidence_id for link in payment.evidence] == [message.id, photo.id]
        merged = work.transactions_for(user.id).get(suggestion.candidate_id)
        assert merged is not None and merged.status == TransactionStatus.MERGED
        assert work.suggestions_for(user.id).open() == []
