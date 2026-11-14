import uuid
from collections.abc import Callable
from dataclasses import dataclass, replace
from uuid import UUID

from jalada.core.ports import Clock
from jalada.modules.evidence.domain.evidence import Evidence, EvidenceStatus
from jalada.modules.ledger.application.transaction_mirror import mirror_entry
from jalada.modules.ledger.domain.categories import CATEGORIES, Purpose
from jalada.modules.ledger.domain.entries import (
    Correction,
    Entry,
    EntryKind,
    EntryStatus,
    counterparty_key,
    missing_fields,
)
from jalada.shared.errors import EntryNotFound, EvidenceNotFound, InvalidEntry
from jalada.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class ReviewItem:
    """One thing waiting for the user: an entry to check, or evidence with no entry yet."""

    evidence: Evidence
    entry: Entry | None


class EntryReview:
    """Confirming, correcting and hand-entering ledger entries. Every change is kept."""

    def __init__(self, unit_of_work: Callable[[], UnitOfWork], clock: Clock) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    def queue(self, user_id: UUID, limit: int = 100) -> list[ReviewItem]:
        with self._unit_of_work() as work:
            evidence = work.evidence_for(user_id)
            entries = work.entries_for(user_id).pending(limit)
            items = [
                ReviewItem(e, entry) for entry in entries if (e := evidence.get(entry.evidence_id))
            ]
            items += [ReviewItem(e, None) for e in evidence.needing_entry(limit)]
        return sorted(items, key=lambda item: item.evidence.received_at)

    def confirm(self, user_id: UUID, entry_id: UUID, correction: Correction | None = None) -> Entry:
        with self._unit_of_work() as work:
            entry = work.entries_for(user_id).get(entry_id)
            if entry is None:
                raise EntryNotFound
            if entry.status == EntryStatus.CONFIRMED and correction is None:
                return entry
            confirmed = self._confirmed(_corrected(entry, correction or Correction()))
            work.entries_for(user_id).update(confirmed)
            mirror_entry(work, confirmed)
            work.entries_for(user_id).add_revision(entry, confirmed, self._clock.now())
            self._learn(work, user_id, confirmed)
            work.evidence_for(user_id).set_status(entry.evidence_id, EvidenceStatus.CONFIRMED)
            work.commit()
        return confirmed

    def enter_by_hand(self, user_id: UUID, evidence_id: UUID, values: Correction) -> Entry:
        """For evidence nothing could read: the user types the entry in."""
        with self._unit_of_work() as work:
            if work.evidence_for(user_id).get(evidence_id) is None:
                raise EvidenceNotFound
            if work.entries_for(user_id).for_evidence(evidence_id):
                raise InvalidEntry("This evidence already has an entry.")
            blank = Entry(
                uuid.uuid4(),
                user_id,
                evidence_id,
                None,
                EntryKind.TRANSACTION,
                EntryStatus.NEEDS_REVIEW,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                Purpose.UNSURE,
                None,
                1.0,
                self._clock.now(),
            )
            entry = self._confirmed(_corrected(blank, values))
            work.entries_for(user_id).add(entry)
            mirror_entry(work, entry)
            self._learn(work, user_id, entry)
            work.evidence_for(user_id).set_status(evidence_id, EvidenceStatus.CONFIRMED)
            work.commit()
        return entry

    def mark_not_a_transaction(self, user_id: UUID, evidence_id: UUID) -> None:
        """The evidence leaves the review queue. Its entry, if any, is kept as rejected."""
        with self._unit_of_work() as work:
            if work.evidence_for(user_id).get(evidence_id) is None:
                raise EvidenceNotFound
            entry = work.entries_for(user_id).for_evidence(evidence_id)
            if entry and entry.status == EntryStatus.CONFIRMED:
                raise InvalidEntry("This is already in your ledger.")
            if entry and entry.status != EntryStatus.REJECTED:
                rejected = replace(entry, status=EntryStatus.REJECTED)
                work.entries_for(user_id).update(rejected)
                mirror_entry(work, rejected)
                work.entries_for(user_id).add_revision(entry, rejected, self._clock.now())
            work.evidence_for(user_id).set_status(evidence_id, EvidenceStatus.NOT_A_TRANSACTION)
            work.commit()

    def _confirmed(self, entry: Entry) -> Entry:
        missing = missing_fields(entry)
        if missing:
            raise InvalidEntry(f"Add the {', '.join(missing)} before confirming.")
        category = CATEGORIES[entry.category or ""]
        if category.direction != entry.direction:
            raise InvalidEntry("That category does not fit money going this way.")
        return replace(
            entry,
            status=EntryStatus.CONFIRMED,
            purpose=category.purpose,
            confirmed_at=self._clock.now(),
        )

    @staticmethod
    def _learn(work: UnitOfWork, user_id: UUID, entry: Entry) -> None:
        if entry.counterparty and entry.category:
            key = counterparty_key(entry.counterparty)
            work.preferences_for(user_id).remember(key, entry.category, entry.purpose)


def _corrected(entry: Entry, correction: Correction) -> Entry:
    if correction.category is not None and correction.category not in CATEGORIES:
        raise InvalidEntry("That category does not exist.")
    if correction.amount_cents is not None and correction.amount_cents <= 0:
        raise InvalidEntry("The amount must be more than zero.")
    changes = {name: value for name, value in vars(correction).items() if value is not None}
    if "counterparty" in changes:
        changes["counterparty"] = " ".join(changes["counterparty"].split())[:200] or None
    return replace(entry, **changes)
