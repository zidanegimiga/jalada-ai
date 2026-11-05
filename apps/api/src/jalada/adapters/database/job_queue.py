from collections.abc import Callable
from datetime import datetime

from sqlalchemy.orm import Session as DbSession

from jalada.adapters.database.tables import JobRow


class SqlJobQueue:
    """Jobs live in Postgres, written in the same transaction as the work that creates them."""

    def __init__(self, db: DbSession, now: Callable[[], datetime]) -> None:
        self._db = db
        self._now = now

    def enqueue(self, kind: str, payload: dict[str, str]) -> None:
        self._db.add(JobRow(kind=kind, payload=payload, status="queued", run_after=self._now()))
