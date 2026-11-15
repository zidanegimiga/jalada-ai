"""Saving what the pipeline proposes, with its audit event and any suggested matches."""

from dataclasses import dataclass, replace

from jalada.modules.evidence.domain.evidence import Evidence, EvidenceKind
from jalada.modules.ledger.application import history
from jalada.modules.ledger.application.evidence_accounts import account_for
from jalada.modules.ledger.application.suggesting import suggest_same_purchase
from jalada.modules.ledger.domain.audit import Actor, AuditAction
from jalada.modules.ledger.domain.entries import Entry
from jalada.modules.ledger.domain.transactions import TransactionStatus, as_entry
from jalada.modules.pipeline.application.ports import PipelineRun
from jalada.modules.pipeline.application.proposals import proposed_certificate, proposed_payment
from jalada.modules.pipeline.domain.extraction import Classification, Extraction
from jalada.unit_of_work import UnitOfWork

# Added to the reasons given to the user when a suggested match was found.
MAY_MATCH = "may be the same purchase"


@dataclass(frozen=True)
class Proposal:
    # In the shape of an entry, for the message back to the user.
    entry: Entry
    # True when a receipt and a payment may be the same purchase.
    may_match: bool = False


def save_proposal(
    work: UnitOfWork,
    evidence: Evidence,
    run: PipelineRun,
    ready: bool,
    extraction: Extraction,
    classification: Classification,
) -> Proposal:
    """Saves the payment, receipt or certificate the pipeline read."""
    now = run.finished_at
    if extraction.kind == EvidenceKind.WITHHOLDING_CERTIFICATE:
        certificate = proposed_certificate(evidence, run, ready, extraction, classification, now)
        work.entries_for(evidence.user_id).add(certificate)
        history.record_entry(work, None, certificate, Actor.PIPELINE, AuditAction.PROPOSED, now)
        return Proposal(certificate)
    account_id = account_for(work, evidence.user_id, extraction.kind)
    payment = proposed_payment(evidence, run, ready, extraction, classification, account_id, now)
    work.transactions_for(evidence.user_id).add(payment)
    history.record_transaction(work, None, payment, Actor.PIPELINE, AuditAction.PROPOSED, now)
    offered = suggest_same_purchase(work, payment, now)
    if payment.status == TransactionStatus.CANDIDATE:
        # Entries have no candidate status. The message only needs the amount, name and date.
        payment = replace(payment, status=TransactionStatus.NEEDS_REVIEW)
    return Proposal(as_entry(payment), bool(offered))
