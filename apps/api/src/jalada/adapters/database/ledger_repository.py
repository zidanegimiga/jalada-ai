from dataclasses import asdict
from uuid import UUID

from sqlalchemy import exists, select
from sqlalchemy.orm import Session as DbSession

from jalada.adapters.database.tables import CounterpartyPreferenceRow, EntryRow
from jalada.domain.categories import Purpose
from jalada.domain.entries import Entry
from jalada.pipeline.classifier import Preference


class SqlEntryRepository:
    """Ledger entries for one user. Every query filters by that user."""

    def __init__(self, db: DbSession, user_id: UUID) -> None:
        self._db = db
        self._user_id = user_id

    def add(self, entry: Entry) -> None:
        if entry.user_id != self._user_id:
            raise PermissionError("Entry belongs to another user")
        self._db.add(EntryRow(**asdict(entry)))
        self._db.flush()

    def has_mpesa_code(self, code: str) -> bool:
        return self._exists(EntryRow.mpesa_code == code)

    def has_certificate_serial(self, serial: str) -> bool:
        return self._exists(EntryRow.certificate_serial == serial)

    def _exists(self, condition: object) -> bool:
        query = select(exists().where(EntryRow.user_id == self._user_id, condition))  # type: ignore[arg-type]
        return bool(self._db.scalar(query))


class SqlPreferenceRepository:
    def __init__(self, db: DbSession, user_id: UUID) -> None:
        self._db = db
        self._user_id = user_id

    def all(self) -> dict[str, Preference]:
        rows = self._db.scalars(
            select(CounterpartyPreferenceRow).where(
                CounterpartyPreferenceRow.user_id == self._user_id
            )
        )
        return {
            row.counterparty_key: Preference(row.category, Purpose(row.purpose), row.times_used)
            for row in rows
        }
