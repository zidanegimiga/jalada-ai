import uuid
from collections.abc import Callable
from dataclasses import dataclass
from uuid import UUID

from jalada.core.ports import Clock
from jalada.modules.evidence.application.ports import EvidenceStore
from jalada.modules.evidence.domain.evidence import (
    MAX_FILE_BYTES,
    MAX_TEXT_CHARACTERS,
    TEXT_CONTENT_TYPE,
    Evidence,
    EvidenceKind,
    EvidenceSource,
    EvidenceStatus,
    detect_file_type,
    fingerprint,
)
from jalada.shared.errors import (
    EmptyEvidence,
    EvidenceNotFound,
    FileTooLarge,
    UnsupportedFile,
)
from jalada.unit_of_work import UnitOfWork

PROCESS_EVIDENCE_JOB = "process_evidence"


@dataclass(frozen=True)
class Captured:
    evidence: Evidence
    # True when the same file or text was already captured; nothing new was stored.
    duplicate: bool


class EvidenceCapture:
    """Accepts files and pasted text, stores them encrypted, and queues them for processing."""

    def __init__(
        self, unit_of_work: Callable[[], UnitOfWork], store: EvidenceStore, clock: Clock
    ) -> None:
        self._unit_of_work = unit_of_work
        self._store = store
        self._clock = clock

    def capture_file(self, user_id: UUID, data: bytes, source: EvidenceSource) -> Captured:
        if len(data) > MAX_FILE_BYTES:
            raise FileTooLarge
        content_type = detect_file_type(data)
        if content_type is None:
            raise UnsupportedFile
        return self._capture(user_id, data, content_type, source)

    def capture_text(self, user_id: UUID, text: str, source: EvidenceSource) -> Captured:
        text = text.strip()
        if not text:
            raise EmptyEvidence
        if len(text) > MAX_TEXT_CHARACTERS:
            raise FileTooLarge
        return self._capture(user_id, text.encode(), TEXT_CONTENT_TYPE, source)

    def list_recent(self, user_id: UUID, limit: int = 50) -> list[Evidence]:
        with self._unit_of_work() as work:
            return work.evidence_for(user_id).list_recent(limit)

    def get(self, user_id: UUID, evidence_id: UUID) -> Evidence:
        with self._unit_of_work() as work:
            evidence = work.evidence_for(user_id).get(evidence_id)
        if evidence is None:
            raise EvidenceNotFound
        return evidence

    def read_original(self, user_id: UUID, evidence_id: UUID) -> tuple[Evidence, bytes]:
        evidence = self.get(user_id, evidence_id)
        return evidence, self._store.get(evidence.id, user_id, evidence.encryption_key_id)

    def _capture(
        self, user_id: UUID, data: bytes, content_type: str, source: EvidenceSource
    ) -> Captured:
        sha256 = fingerprint(data)
        with self._unit_of_work() as work:
            existing = work.evidence_for(user_id).get_by_fingerprint(sha256)
        if existing:
            return Captured(existing, duplicate=True)
        evidence = Evidence(
            id=uuid.uuid4(),
            user_id=user_id,
            source=source,
            kind=EvidenceKind.UNKNOWN,
            status=EvidenceStatus.RECEIVED,
            content_type=content_type,
            size_bytes=len(data),
            sha256=sha256,
            encryption_key_id=self._store.key_id,
            received_at=self._clock.now(),
        )
        # Store the bytes first, so a queued job never points at a missing file.
        self._store.put(evidence.id, user_id, data)
        try:
            with self._unit_of_work() as work:
                work.evidence_for(user_id).add(evidence)
                work.jobs.enqueue(
                    PROCESS_EVIDENCE_JOB,
                    {"evidence_id": str(evidence.id), "user_id": str(user_id)},
                )
                work.commit()
        except Exception:
            self._store.delete(evidence.id, user_id)
            raise
        return Captured(evidence, duplicate=False)
