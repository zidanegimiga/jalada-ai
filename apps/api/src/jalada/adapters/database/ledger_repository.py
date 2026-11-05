from dataclasses import asdict
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Select, case, exists, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session as DbSession

from jalada.adapters.database.tables import CounterpartyPreferenceRow, EntryRevisionRow, EntryRow
from jalada.domain.categories import Direction, Purpose
from jalada.domain.entries import Entry, EntryKind, EntryStatus
from jalada.pipeline.classifier import Preference

PENDING = [EntryStatus.PROPOSED, EntryStatus.NEEDS_REVIEW]


class SqlEntryRepository:
    """Ledger entries for one user. Every query starts from `_mine`, which filters by user."""

    def __init__(self, db: DbSession, user_id: UUID) -> None:
        self._db = db
        self._user_id = user_id

    def add(self, entry: Entry) -> None:
        self._check_owner(entry)
        self._db.add(EntryRow(**asdict(entry)))
        self._db.flush()

    def get(self, entry_id: UUID) -> Entry | None:
        return self._one(self._mine().where(EntryRow.id == entry_id))

    def for_evidence(self, evidence_id: UUID) -> Entry | None:
        return self._one(self._mine().where(EntryRow.evidence_id == evidence_id))

    def update(self, entry: Entry) -> None:
        self._check_owner(entry)
        values = {k: v for k, v in asdict(entry).items() if k not in ("id", "user_id")}
        self._db.execute(
            update(EntryRow)
            .where(EntryRow.user_id == self._user_id, EntryRow.id == entry.id)
            .values(**values)
        )

    def add_revision(self, before: Entry, after: Entry, changed_at: datetime) -> None:
        self._check_owner(after)
        self._db.add(
            EntryRevisionRow(
                entry_id=after.id,
                before=_record(before),
                after=_record(after),
                changed_at=changed_at,
            )
        )

    def pending(self, limit: int) -> list[Entry]:
        query = self._mine().where(EntryRow.status.in_(PENDING)).limit(limit)
        return [_to_entry(row) for row in self._db.scalars(query)]

    def has_mpesa_code(self, code: str) -> bool:
        return self._exists(EntryRow.mpesa_code == code)

    def has_certificate_serial(self, serial: str) -> bool:
        return self._exists(EntryRow.certificate_serial == serial)

    def _mine(self) -> Select[EntryRow]:
        return select(EntryRow).where(EntryRow.user_id == self._user_id)

    def _one(self, query: Select[EntryRow]) -> Entry | None:
        row = self._db.scalars(query).one_or_none()
        return _to_entry(row) if row else None

    def _exists(self, condition: Any) -> bool:
        return bool(
            self._db.scalar(select(exists().where(EntryRow.user_id == self._user_id, condition)))
        )

    def _check_owner(self, entry: Entry) -> None:
        if entry.user_id != self._user_id:
            raise PermissionError("Entry belongs to another user")


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

    def remember(self, counterparty_key: str, category: str, purpose: Purpose) -> None:
        """Save the user's choice. Choosing the same again makes it count for more."""
        row = CounterpartyPreferenceRow
        statement = insert(row).values(
            user_id=self._user_id,
            counterparty_key=counterparty_key,
            category=category,
            purpose=purpose,
            times_used=1,
        )
        # In ON CONFLICT, the table's columns are the row already saved.
        same_choice = (row.category == category) & (row.purpose == purpose)
        self._db.execute(
            statement.on_conflict_do_update(
                index_elements=["user_id", "counterparty_key"],
                set_={
                    "category": category,
                    "purpose": purpose,
                    # A different choice starts counting again from one.
                    "times_used": case((same_choice, row.times_used + 1), else_=1),
                },
            )
        )


def _record(entry: Entry) -> dict[str, Any]:
    return {k: (str(v) if v is not None else None) for k, v in asdict(entry).items()}


def _to_entry(row: EntryRow) -> Entry:
    return Entry(
        id=row.id,
        user_id=row.user_id,
        evidence_id=row.evidence_id,
        run_id=row.run_id,
        kind=EntryKind(row.kind),
        status=EntryStatus(row.status),
        occurred_on=row.occurred_on,
        direction=Direction(row.direction) if row.direction else None,
        amount_cents=row.amount_cents,
        counterparty=row.counterparty,
        reference=row.reference,
        mpesa_code=row.mpesa_code,
        certificate_serial=row.certificate_serial,
        tax_withheld_cents=row.tax_withheld_cents,
        purpose=Purpose(row.purpose),
        category=row.category,
        confidence=row.confidence,
        created_at=row.created_at,
        confirmed_at=row.confirmed_at,
    )
