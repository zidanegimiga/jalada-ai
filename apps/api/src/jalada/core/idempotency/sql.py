from datetime import datetime

from sqlalchemy import delete, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DbSession
from sqlalchemy.orm import sessionmaker

from jalada.core.idempotency.ports import Answer, Attempt, Seen
from jalada.core.idempotency.tables import IdempotencyKeyRow as Row


class SqlIdempotencyStore:
    """Kept answers in Postgres. Its own short transactions, apart from the request's work."""

    def __init__(self, session_factory: sessionmaker[DbSession]) -> None:
        self._sessions = session_factory

    def begin(
        self,
        owner: str,
        key: str,
        fingerprint: str,
        now: datetime,
        expired_before: datetime,
        abandoned_before: datetime,
    ) -> Attempt:
        try:
            with self._sessions.begin() as db:
                _clear_old(db, owner, key, expired_before, abandoned_before)
                claimed = db.execute(
                    insert(Row)
                    .values(owner_hash=owner, key=key, fingerprint=fingerprint, created_at=now)
                    .on_conflict_do_nothing()
                    .returning(Row.key)
                ).first()
                if claimed:
                    return Attempt(Seen.NEW)
                return _compare(db.get(Row, (owner, key)), fingerprint)
        except IntegrityError:
            # The owner must be a session: anything else is refused by the foreign key.
            return Attempt(Seen.NO_SESSION)

    def keep(self, owner: str, key: str, answer: Answer) -> None:
        with self._sessions.begin() as db:
            db.execute(
                update(Row)
                .where(Row.owner_hash == owner, Row.key == key)
                .values(status=answer.status, content_type=answer.content_type, body=answer.body)
            )

    def drop(self, owner: str, key: str) -> None:
        with self._sessions.begin() as db:
            db.execute(delete(Row).where(Row.owner_hash == owner, Row.key == key))


def _clear_old(
    db: DbSession, owner: str, key: str, expired_before: datetime, abandoned_before: datetime
) -> None:
    """Drops this session's answers past keeping, and a first try that never finished."""
    db.execute(delete(Row).where(Row.owner_hash == owner, Row.created_at < expired_before))
    db.execute(
        delete(Row).where(
            Row.owner_hash == owner,
            Row.key == key,
            Row.status.is_(None),
            Row.created_at < abandoned_before,
        )
    )


def _compare(row: Row | None, fingerprint: str) -> Attempt:
    if row is None:
        return Attempt(Seen.RUNNING)
    if row.fingerprint != fingerprint:
        return Attempt(Seen.DIFFERENT)
    if row.status is None:
        return Attempt(Seen.RUNNING)
    return Attempt(Seen.ANSWERED, Answer(row.status, row.content_type, row.body or b""))
