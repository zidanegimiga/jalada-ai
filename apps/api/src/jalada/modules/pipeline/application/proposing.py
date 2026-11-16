"""Saving what the pipeline proposes, with its audit event and any suggested matches."""

from dataclasses import dataclass

from jalada.modules.evidence.domain.evidence import Evidence, EvidenceKind
from jalada.modules.ledger.application import history
from jalada.modules.ledger.application.evidence_accounts import account_for
from jalada.modules.ledger.application.suggesting import suggest_same_purchase
from jalada.modules.ledger.domain.audit import Actor, AuditAction
from jalada.modules.ledger.domain.entries import Entry
from jalada.modules.ledger.domain.transactions import (
    Transaction,
    TransactionStatus,
    as_entry,
    candidate_as_entry,
)
from jalada.modules.ledger.domain.transfers import as_transfer, own_account_for
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
    if classification.source == "own_account":
        payment = _as_transfer(work, payment)
    work.transactions_for(evidence.user_id).add(payment)
    history.record_transaction(work, None, payment, Actor.PIPELINE, AuditAction.PROPOSED, now)
    offered = suggest_same_purchase(work, payment, now)
    waiting = payment.status == TransactionStatus.CANDIDATE
    shown = candidate_as_entry(payment) if waiting else as_entry(payment)
    return Proposal(shown, bool(offered))


def _as_transfer(work: UnitOfWork, payment: Transaction) -> Transaction:
    """A payment to or from an account the user said is theirs, proposed as a transfer."""
    account = own_account_for(payment, work.money_accounts_for(payment.user_id).all())
    return as_transfer(payment, account) if account else payment
