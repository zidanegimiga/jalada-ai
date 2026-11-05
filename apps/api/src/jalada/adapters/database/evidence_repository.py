from uuid import UUID

from sqlalchemy import Select, exists, select, update
from sqlalchemy.orm import Session as DbSession

from jalada.adapters.database.tables import EntryRow, EvidenceRow
from jalada.domain.evidence import Evidence, EvidenceKind, EvidenceSource, EvidenceStatus


class SqlEvidenceRepository:
    """Bound to one user. Every query starts from `_mine`, so none can skip the user filter."""

    def __init__(self, db: DbSession, user_id: UUID) -> None:
        self._db = db
        self._user_id = user_id

    def add(self, evidence: Evidence) -> None:
        if evidence.user_id != self._user_id:
            raise PermissionError("Evidence belongs to another user")
        self._db.add(
            EvidenceRow(
                id=evidence.id,
                user_id=evidence.user_id,
                source=evidence.source,
                kind=evidence.kind,
                status=evidence.status,
                content_type=evidence.content_type,
                size_bytes=evidence.size_bytes,
                sha256=evidence.sha256,
                encryption_key_id=evidence.encryption_key_id,
                received_at=evidence.received_at,
            )
        )
        self._db.flush()

    def get(self, evidence_id: UUID) -> Evidence | None:
        return self._one(self._mine().where(EvidenceRow.id == evidence_id))

    def get_by_fingerprint(self, sha256: str) -> Evidence | None:
        return self._one(self._mine().where(EvidenceRow.sha256 == sha256))

    def list_recent(self, limit: int) -> list[Evidence]:
        query = self._mine().order_by(EvidenceRow.received_at.desc()).limit(limit)
        return [_to_evidence(row) for row in self._db.scalars(query)]

    def set_outcome(self, evidence_id: UUID, kind: EvidenceKind, status: EvidenceStatus) -> None:
        self._db.execute(
            update(EvidenceRow)
            .where(EvidenceRow.user_id == self._user_id, EvidenceRow.id == evidence_id)
            .values(kind=kind, status=status)
        )

    def set_status(self, evidence_id: UUID, status: EvidenceStatus) -> None:
        self._db.execute(
            update(EvidenceRow)
            .where(EvidenceRow.user_id == self._user_id, EvidenceRow.id == evidence_id)
            .values(status=status)
        )

    def needing_entry(self, limit: int) -> list[Evidence]:
        """Evidence nothing could read: it needs the user to type the entry in."""
        has_entry = exists().where(EntryRow.evidence_id == EvidenceRow.id)
        query = (
            self._mine()
            .where(
                EvidenceRow.status.in_([EvidenceStatus.NEEDS_REVIEW, EvidenceStatus.FAILED]),
                ~has_entry,
            )
            .order_by(EvidenceRow.received_at)
            .limit(limit)
        )
        return [_to_evidence(row) for row in self._db.scalars(query)]

    def _mine(self) -> Select[EvidenceRow]:
        return select(EvidenceRow).where(EvidenceRow.user_id == self._user_id)

    def _one(self, query: Select[EvidenceRow]) -> Evidence | None:
        row = self._db.scalars(query).one_or_none()
        return _to_evidence(row) if row else None


def _to_evidence(row: EvidenceRow) -> Evidence:
    return Evidence(
        id=row.id,
        user_id=row.user_id,
        source=EvidenceSource(row.source),
        kind=EvidenceKind(row.kind),
        status=EvidenceStatus(row.status),
        content_type=row.content_type,
        size_bytes=row.size_bytes,
        sha256=row.sha256,
        encryption_key_id=row.encryption_key_id,
        received_at=row.received_at,
    )
