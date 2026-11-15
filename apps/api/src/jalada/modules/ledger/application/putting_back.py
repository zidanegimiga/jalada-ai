"""Putting back evidence the user marked "Not a transaction" by mistake."""

from dataclasses import replace
from datetime import datetime
from uuid import UUID

from jalada.modules.evidence.domain.evidence import EvidenceStatus
from jalada.modules.ledger.application import history
from jalada.modules.ledger.domain.audit import Actor, AuditAction
from jalada.modules.ledger.domain.entries import EntryStatus
from jalada.modules.ledger.domain.putting_back import (
    EVIDENCE_STATUS,
    WAITING,
    status_before_rejection,
)
from jalada.modules.ledger.domain.transactions import TransactionStatus
from jalada.shared.errors import EvidenceNotFound, InvalidEntry
from jalada.unit_of_work import UnitOfWork


def put_back(work: UnitOfWork, user_id: UUID, evidence_id: UUID, now: datetime) -> None:
    """The evidence and its payment or certificate return to where they were, and the
    change is kept in the audit trail."""
    evidence = work.evidence_for(user_id).get(evidence_id)
    if evidence is None:
        raise EvidenceNotFound
    if evidence.status != EvidenceStatus.NOT_A_TRANSACTION:
        raise InvalidEntry("This is not marked as not a transaction.")
    status = _put_back_payment(work, user_id, evidence_id, now)
    if status is None:
        status = _put_back_certificate(work, user_id, evidence_id, now)
    work.evidence_for(user_id).set_status(evidence_id, EVIDENCE_STATUS[status or WAITING])


def _put_back_payment(
    work: UnitOfWork, user_id: UUID, evidence_id: UUID, now: datetime
) -> str | None:
    payment = work.transactions_for(user_id).for_evidence(evidence_id)
    if payment is None or payment.status != TransactionStatus.REJECTED:
        return None
    status = status_before_rejection(work.audit_for(user_id).for_subject(payment.id))
    restored = replace(payment, status=TransactionStatus(status))
    work.transactions_for(user_id).update(restored)
    history.record_transaction(work, payment, restored, Actor.USER, AuditAction.RESTORED, now)
    return status


def _put_back_certificate(
    work: UnitOfWork, user_id: UUID, evidence_id: UUID, now: datetime
) -> str | None:
    entry = work.entries_for(user_id).for_evidence(evidence_id)
    if entry is None or entry.status != EntryStatus.REJECTED:
        return None
    status = status_before_rejection(work.audit_for(user_id).for_subject(entry.id))
    restored = replace(entry, status=EntryStatus(status))
    work.entries_for(user_id).update(restored)
    work.entries_for(user_id).add_revision(entry, restored, now)
    history.record_entry(work, entry, restored, Actor.USER, AuditAction.RESTORED, now)
    return status
