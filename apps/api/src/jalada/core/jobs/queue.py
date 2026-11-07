from collections.abc import Callable
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import delete, or_, select, update
from sqlalchemy.orm import Session as DbSession

from jalada.core.jobs.ports import Job
from jalada.core.jobs.tables import JobRow


class SqlJobQueue:
    """Jobs live in Postgres, written in the same transaction as the work that creates them."""

    def __init__(self, db: DbSession, now: Callable[[], datetime]) -> None:
        self._db = db
        self._now = now

    def enqueue(self, kind: str, payload: dict[str, str]) -> None:
        self._db.add(JobRow(kind=kind, payload=payload, status="queued", run_after=self._now()))

    def claim(self, now: datetime, lock_seconds: int) -> Job | None:
        """The oldest due job. A job whose lock expired (a crashed worker) is due again.

        SKIP LOCKED lets several workers claim at once without taking the same job.
        """
        due = or_(
            (JobRow.status == "queued") & (JobRow.run_after <= now),
            (JobRow.status == "running") & (JobRow.locked_until < now),
        )
        query = (
            select(JobRow)
            .where(due)
            .order_by(JobRow.run_after)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        row = self._db.scalars(query).one_or_none()
        if row is None:
            return None
        row.status = "running"
        row.attempts += 1
        row.locked_until = now + timedelta(seconds=lock_seconds)
        return Job(row.id, row.kind, dict(row.payload), row.attempts)

    def complete(self, job_id: int) -> None:
        self._db.execute(
            update(JobRow).where(JobRow.id == job_id).values(status="done", locked_until=None)
        )

    def fail(self, job_id: int, error: str, retry_at: datetime | None) -> None:
        values: dict[str, object] = {"last_error": error, "locked_until": None}
        if retry_at is None:
            values |= {"status": "failed"}
        else:
            values |= {"status": "queued", "run_after": retry_at}
        self._db.execute(update(JobRow).where(JobRow.id == job_id).values(**values))

    def discard_for(self, user_id: UUID) -> None:
        """Jobs hold the user's id in their payload rather than a foreign key, so they go here."""
        self._db.execute(delete(JobRow).where(JobRow.payload["user_id"].astext == str(user_id)))
