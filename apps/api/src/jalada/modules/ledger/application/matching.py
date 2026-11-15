"""Linking evidence to the payment it describes when the match is exact."""

from dataclasses import replace
from datetime import date, datetime

from jalada.modules.evidence.domain.evidence import Evidence, EvidenceKind
from jalada.modules.ledger.application import history
from jalada.modules.ledger.domain.audit import Actor, AuditAction
from jalada.modules.ledger.domain.categories import Direction
from jalada.modules.ledger.domain.matching import is_exact_match
from jalada.modules.ledger.domain.transactions import (
    EvidenceLink,
    LinkedBy,
    Transaction,
    role_for,
)
from jalada.unit_of_work import UnitOfWork


def link_exact_match(
    work: UnitOfWork,
    evidence: Evidence,
    kind: EvidenceKind,
    code: str | None,
    amount_cents: int | None,
    direction: Direction | None,
    occurred_on: date | None,
    now: datetime,
) -> Transaction | None:
    """Links the evidence to the payment with the same code, amount, direction and date, and
    returns that payment. None when there is no exact match: the evidence is then left as it
    was. Linking never confirms anything."""
    if not code:
        return None
    payment = work.transactions_for(evidence.user_id).with_payment_code(code)
    if payment is None or not is_exact_match(payment, code, amount_cents, direction, occurred_on):
        return None
    if evidence.id in {link.evidence_id for link in payment.evidence}:
        return payment
    link = EvidenceLink(evidence.id, role_for(kind), LinkedBy.EXACT, now)
    linked = replace(payment, evidence=(*payment.evidence, link))
    work.transactions_for(evidence.user_id).update(linked)
    history.record_transaction(work, payment, linked, Actor.PIPELINE, AuditAction.LINKED, now)
    return linked
