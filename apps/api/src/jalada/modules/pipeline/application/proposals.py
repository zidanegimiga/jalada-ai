"""What the pipeline proposes from what it read: a payment, or a withholding certificate,
which is still an entry. Nothing here is confirmed; the user confirms every one."""

import uuid
from datetime import datetime
from uuid import UUID

from jalada.modules.evidence.domain.evidence import Evidence
from jalada.modules.ledger.domain.entries import Entry, EntryKind, EntryStatus
from jalada.modules.ledger.domain.transactions import (
    EvidenceLink,
    LinkedBy,
    Transaction,
    TransactionKind,
    TransactionLine,
    TransactionStatus,
    role_for,
)
from jalada.modules.pipeline.application.ports import PipelineRun
from jalada.modules.pipeline.domain.extraction import Classification, Extraction


def proposed_payment(
    evidence: Evidence,
    run: PipelineRun,
    ready: bool,
    extraction: Extraction,
    classification: Classification,
    account_id: UUID | None,
    now: datetime,
) -> Transaction:
    """`ready` when nothing needs a look, so the user can confirm it as it is."""
    return Transaction(
        id=uuid.uuid4(),
        user_id=evidence.user_id,
        account_id=account_id,
        kind=TransactionKind.PAYMENT,
        status=TransactionStatus.PROPOSED if ready else TransactionStatus.NEEDS_REVIEW,
        occurred_on=extraction.occurred_on,
        direction=extraction.direction,
        amount_cents=extraction.amount_cents,
        counterparty=extraction.counterparty,
        reference=extraction.reference,
        payment_code=extraction.mpesa_code,
        confidence=classification.confidence,
        run_id=run.id,
        created_at=now,
        confirmed_at=None,
        lines=(
            TransactionLine(
                extraction.amount_cents, classification.category, classification.purpose
            ),
        ),
        evidence=(EvidenceLink(evidence.id, role_for(extraction.kind), LinkedBy.PIPELINE, now),),
    )


def proposed_certificate(
    evidence: Evidence,
    run: PipelineRun,
    ready: bool,
    extraction: Extraction,
    classification: Classification,
    now: datetime,
) -> Entry:
    return Entry(
        id=uuid.uuid4(),
        user_id=evidence.user_id,
        evidence_id=evidence.id,
        run_id=run.id,
        kind=EntryKind.WITHHOLDING_CERTIFICATE,
        status=EntryStatus.PROPOSED if ready else EntryStatus.NEEDS_REVIEW,
        occurred_on=extraction.occurred_on,
        direction=extraction.direction,
        amount_cents=extraction.amount_cents,
        counterparty=extraction.counterparty,
        reference=extraction.reference,
        mpesa_code=extraction.mpesa_code,
        certificate_serial=extraction.certificate_serial,
        tax_withheld_cents=extraction.tax_withheld_cents,
        purpose=classification.purpose,
        category=classification.category,
        confidence=classification.confidence,
        created_at=now,
        payer_tax_number=extraction.payer_tax_number,
    )
