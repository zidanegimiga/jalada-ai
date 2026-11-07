from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from jalada.modules.evidence.domain.evidence import (
    MAX_TEXT_CHARACTERS,
    Evidence,
    EvidenceKind,
    EvidenceSource,
    EvidenceStatus,
)


class PasteRequest(BaseModel):
    text: str = Field(min_length=1, max_length=MAX_TEXT_CHARACTERS)


class EvidenceResponse(BaseModel):
    id: UUID
    source: EvidenceSource
    kind: EvidenceKind
    status: EvidenceStatus
    content_type: str
    size_bytes: int
    received_at: datetime
    duplicate: bool = False

    @classmethod
    def from_evidence(cls, evidence: Evidence, duplicate: bool = False) -> "EvidenceResponse":
        return cls(
            id=evidence.id,
            source=evidence.source,
            kind=evidence.kind,
            status=evidence.status,
            content_type=evidence.content_type,
            size_bytes=evidence.size_bytes,
            received_at=evidence.received_at,
            duplicate=duplicate,
        )


class EvidenceList(BaseModel):
    items: list[EvidenceResponse]
