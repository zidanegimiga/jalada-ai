"""Confirming, correcting, typing in and rejecting payments, which are transactions. Each
change is saved with its audit event and teaches the classifier."""

import uuid
from dataclasses import replace
from datetime import datetime

from jalada.modules.evidence.domain.evidence import Evidence, EvidenceStatus
from jalada.modules.ledger.application import history
from jalada.modules.ledger.application.evidence_accounts import account_for
from jalada.modules.ledger.domain import payment_review
from jalada.modules.ledger.domain.audit import Actor, AuditAction
from jalada.modules.ledger.domain.categories import Purpose
from jalada.modules.ledger.domain.entries import Correction, counterparty_key
from jalada.modules.ledger.domain.transactions import (
    EvidenceLink,
    LinkedBy,
    Transaction,
    TransactionKind,
    TransactionLine,
    TransactionStatus,
    role_for,
)
from jalada.shared.errors import InvalidEntry
from jalada.unit_of_work import UnitOfWork


def confirm(
    work: UnitOfWork, payment: Transaction, correction: Correction, now: datetime
) -> Transaction:
    done = _checked(payment, correction, now)
    work.transactions_for(payment.user_id).update(done)
    action = AuditAction.CORRECTED if any(vars(correction).values()) else AuditAction.CONFIRMED
    history.record_transaction(work, payment, done, Actor.USER, action, now)
    _learn(work, done)
    work.evidence_for(done.user_id).set_status(
        done.evidence[0].evidence_id, EvidenceStatus.CONFIRMED
    )
    return done


def enter(work: UnitOfWork, evidence: Evidence, values: Correction, now: datetime) -> Transaction:
    """A payment typed in by the user for evidence nothing could read."""
    blank = Transaction(
        id=uuid.uuid4(),
        user_id=evidence.user_id,
        account_id=account_for(work, evidence.user_id, evidence.kind),
        kind=TransactionKind.PAYMENT,
        status=TransactionStatus.NEEDS_REVIEW,
        occurred_on=None,
        direction=None,
        amount_cents=None,
        counterparty=None,
        reference=None,
        payment_code=None,
        confidence=1.0,
        run_id=None,
        created_at=now,
        confirmed_at=None,
        lines=(TransactionLine(None, None, Purpose.UNSURE),),
        evidence=(EvidenceLink(evidence.id, role_for(evidence.kind), LinkedBy.USER, now),),
    )
    done = _checked(blank, values, now)
    work.transactions_for(evidence.user_id).add(done)
    history.record_transaction(work, None, done, Actor.USER, AuditAction.ENTERED, now)
    _learn(work, done)
    work.evidence_for(evidence.user_id).set_status(evidence.id, EvidenceStatus.CONFIRMED)
    return done


def reject(work: UnitOfWork, payment: Transaction, now: datetime) -> None:
    if payment.status == TransactionStatus.CONFIRMED:
        raise InvalidEntry("This is already in your ledger.")
    if payment.status == TransactionStatus.REJECTED:
        return
    rejected = replace(payment, status=TransactionStatus.REJECTED)
    work.transactions_for(payment.user_id).update(rejected)
    history.record_transaction(work, payment, rejected, Actor.USER, AuditAction.REJECTED, now)


def _checked(payment: Transaction, correction: Correction, now: datetime) -> Transaction:
    try:
        return payment_review.confirmed(payment_review.corrected(payment, correction), now)
    except payment_review.ReviewProblem as problem:
        raise InvalidEntry(str(problem)) from None


def _learn(work: UnitOfWork, payment: Transaction) -> None:
    """A single-line payment teaches the category for its counterparty."""
    if not payment.counterparty or len(payment.lines) != 1:
        return
    [line] = payment.lines
    if line.category:
        key = counterparty_key(payment.counterparty)
        work.preferences_for(payment.user_id).remember(key, line.category, line.purpose)
