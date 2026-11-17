"""One payment with everything kept about it: its evidence and its history."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from jalada.modules.ledger.domain.entries import Entry
from jalada.modules.ledger.domain.entry_history import HistoryItem, history
from jalada.modules.ledger.domain.transactions import EvidenceRole, LinkedBy, as_entry
from jalada.shared.errors import EntryNotFound
from jalada.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class LinkedEvidence:
    evidence_id: UUID
    role: EvidenceRole
    linked_by: LinkedBy
    linked_at: datetime
    content_type: str
    received_at: datetime


@dataclass(frozen=True)
class EntryDetail:
    entry: Entry
    # The certificate this payment is counted on, if the user linked one.
    certificate_id: UUID | None
    evidence: list[LinkedEvidence]
    history: list[HistoryItem]


def entry_detail(work: UnitOfWork, user_id: UUID, entry_id: UUID) -> EntryDetail:
    """Raises EntryNotFound for an id that is not one of this user's payments."""
    transaction = work.transactions_for(user_id).get(entry_id)
    if transaction is None:
        raise EntryNotFound
    store = work.evidence_for(user_id)
    linked = []
    for link in transaction.evidence:
        evidence = store.get(link.evidence_id)
        if evidence is not None:
            linked.append(
                LinkedEvidence(
                    link.evidence_id,
                    link.role,
                    link.linked_by,
                    link.linked_at,
                    evidence.content_type,
                    evidence.received_at,
                )
            )
    return EntryDetail(
        entry=as_entry(transaction),
        certificate_id=work.certificate_payments_for(user_id).links().get(entry_id),
        evidence=linked,
        history=history(work.audit_for(user_id).for_subject(entry_id)),
    )
