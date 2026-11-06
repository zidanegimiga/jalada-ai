from dataclasses import asdict
from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    ColumnElement,
    Select,
    and_,
    exists,
    extract,
    func,
    or_,
    select,
    update,
)
from sqlalchemy.orm import Session as DbSession

from jalada.modules.ledger.adapters.tables import CertificatePaymentRow, EntryRevisionRow, EntryRow
from jalada.modules.ledger.application.ports import Revision
from jalada.modules.ledger.domain.categories import Direction, Purpose
from jalada.modules.ledger.domain.entries import Entry, EntryKind, EntryStatus
from jalada.modules.ledger.domain.ledger import LedgerFilter, LedgerPosition, Total

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

    def confirmed(
        self, filters: LedgerFilter, after: LedgerPosition | None, limit: int
    ) -> list[Entry]:
        query = self._mine().where(EntryRow.status == EntryStatus.CONFIRMED)
        query = query.where(*_conditions(filters))
        if after:
            # Keyset paging: everything strictly older than where the last page ended.
            query = query.where(
                or_(
                    EntryRow.occurred_on < after.occurred_on,
                    and_(EntryRow.occurred_on == after.occurred_on, EntryRow.id < after.entry_id),
                )
            )
        query = query.order_by(EntryRow.occurred_on.desc(), EntryRow.id.desc()).limit(limit)
        return [_to_entry(row) for row in self._db.scalars(query)]

    def monthly_totals(self, year: int) -> list[Total]:
        month = extract("month", EntryRow.occurred_on)
        query = (
            select(month, EntryRow.direction, EntryRow.purpose, func.sum(EntryRow.amount_cents))
            .where(
                EntryRow.user_id == self._user_id,
                EntryRow.status == EntryStatus.CONFIRMED,
                extract("year", EntryRow.occurred_on) == year,
                # A payment linked to a certificate is already counted in its gross amount.
                ~exists().where(CertificatePaymentRow.payment_id == EntryRow.id),
            )
            .group_by(month, EntryRow.direction, EntryRow.purpose)
        )
        return [
            Total(int(m), Direction(str(direction)), Purpose(purpose), int(cents or 0))
            for m, direction, purpose, cents in self._db.execute(query)
        ]

    def all(self) -> list[Entry]:
        query = self._mine().order_by(EntryRow.created_at)
        return [_to_entry(row) for row in self._db.scalars(query)]

    def revisions(self) -> list[Revision]:
        query = (
            select(EntryRevisionRow)
            .join(EntryRow, EntryRow.id == EntryRevisionRow.entry_id)
            .where(EntryRow.user_id == self._user_id)
            .order_by(EntryRevisionRow.changed_at)
        )
        return [
            Revision(row.entry_id, row.before, row.after, row.changed_at)
            for row in self._db.scalars(query)
        ]

    def has_mpesa_code(self, code: str) -> bool:
        return self._exists(EntryRow.mpesa_code == code)

    def has_certificate_serial(self, serial: str) -> bool:
        return self._exists(EntryRow.certificate_serial == serial)

    def incoming(self, start: date, end: date) -> list[Entry]:
        """Confirmed money in between two dates, oldest first."""
        query = self._mine().where(
            EntryRow.status == EntryStatus.CONFIRMED,
            EntryRow.kind == EntryKind.TRANSACTION,
            EntryRow.direction == Direction.IN,
            EntryRow.occurred_on.between(start, end),
        )
        return [_to_entry(row) for row in self._db.scalars(query.order_by(EntryRow.occurred_on))]

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


def _conditions(filters: LedgerFilter) -> list[ColumnElement[bool]]:
    conditions: list[ColumnElement[bool]] = []
    if filters.start:
        conditions.append(EntryRow.occurred_on >= filters.start)
    if filters.end:
        conditions.append(EntryRow.occurred_on <= filters.end)
    if filters.direction:
        conditions.append(EntryRow.direction == filters.direction)
    if filters.purpose:
        conditions.append(EntryRow.purpose == filters.purpose)
    if filters.category:
        conditions.append(EntryRow.category == filters.category)
    return conditions


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
        payer_tax_number=row.payer_tax_number,
    )
