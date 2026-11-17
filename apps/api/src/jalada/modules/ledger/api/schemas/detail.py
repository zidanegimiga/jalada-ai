from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from jalada.modules.ledger.api.schemas.entries import EntryResponse
from jalada.modules.ledger.application.entry_detail import EntryDetail, LinkedEvidence
from jalada.modules.ledger.domain.audit import Actor, AuditAction
from jalada.modules.ledger.domain.entry_history import HistoryItem
from jalada.modules.ledger.domain.transactions import EvidenceRole, LinkedBy


class LinkedEvidenceResponse(BaseModel):
    id: UUID
    role: EvidenceRole
    linked_by: LinkedBy
    linked_at: datetime
    content_type: str
    received_at: datetime

    @classmethod
    def from_link(cls, link: LinkedEvidence) -> "LinkedEvidenceResponse":
        return cls(
            id=link.evidence_id,
            role=link.role,
            linked_by=link.linked_by,
            linked_at=link.linked_at,
            content_type=link.content_type,
            received_at=link.received_at,
        )


class HistoryItemResponse(BaseModel):
    at: datetime
    actor: Actor
    action: AuditAction
    # What a change touched: amount, date, who, direction, category or account.
    changed: list[str]

    @classmethod
    def from_item(cls, item: HistoryItem) -> "HistoryItemResponse":
        return cls(at=item.at, actor=item.actor, action=item.action, changed=list(item.changed))


class EntryDetailResponse(BaseModel):
    """One payment with the evidence linked to it and its history, oldest first."""

    entry: EntryResponse
    evidence: list[LinkedEvidenceResponse]
    history: list[HistoryItemResponse]

    @classmethod
    def from_detail(cls, detail: EntryDetail) -> "EntryDetailResponse":
        entry = EntryResponse.from_entry(detail.entry).model_copy(
            update={"linked_certificate_id": detail.certificate_id}
        )
        return cls(
            entry=entry,
            evidence=[LinkedEvidenceResponse.from_link(e) for e in detail.evidence],
            history=[HistoryItemResponse.from_item(h) for h in detail.history],
        )
