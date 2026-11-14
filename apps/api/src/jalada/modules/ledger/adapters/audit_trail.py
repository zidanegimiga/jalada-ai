from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import Session as DbSession

from jalada.modules.ledger.adapters.tables import AuditEventRow
from jalada.modules.ledger.domain.audit import Actor, AuditAction, AuditEvent, SubjectType


class SqlAuditTrail:
    """One user's audit trail. Every query filters by user, and nothing here updates or
    deletes a row."""

    def __init__(self, db: DbSession, user_id: UUID) -> None:
        self._db = db
        self._user_id = user_id

    def add(self, event: AuditEvent) -> None:
        if event.user_id != self._user_id:
            raise PermissionError("Event belongs to another user")
        self._db.add(
            AuditEventRow(
                id=event.id,
                user_id=event.user_id,
                subject_type=event.subject_type,
                subject_id=event.subject_id,
                actor=event.actor,
                action=event.action,
                before=event.before,
                after=event.after,
                at=event.at,
            )
        )
        self._db.flush()

    def for_subject(self, subject_id: UUID) -> list[AuditEvent]:
        return self._list(self._mine().where(AuditEventRow.subject_id == subject_id))

    def all(self) -> list[AuditEvent]:
        return self._list(self._mine())

    def _mine(self) -> Select[AuditEventRow]:
        return select(AuditEventRow).where(AuditEventRow.user_id == self._user_id)

    def _list(self, query: Select[AuditEventRow]) -> list[AuditEvent]:
        rows = self._db.scalars(query.order_by(AuditEventRow.at, AuditEventRow.seq))
        return [
            AuditEvent(
                row.id,
                row.user_id,
                SubjectType(row.subject_type),
                row.subject_id,
                Actor(row.actor),
                AuditAction(row.action),
                row.before,
                row.after,
                row.at,
            )
            for row in rows
        ]
