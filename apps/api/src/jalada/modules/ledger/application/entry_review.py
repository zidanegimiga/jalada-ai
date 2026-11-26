from collections.abc import Callable, Sequence
from dataclasses import replace
from uuid import UUID

from jalada.core.ports import Clock
from jalada.modules.evidence.domain.evidence import EvidenceStatus
from jalada.modules.ledger.application import confirm_all, history, payment_review, putting_back
from jalada.modules.ledger.application.review_queue import ReviewItem, review_queue
from jalada.modules.ledger.domain.audit import Actor, AuditAction
from jalada.modules.ledger.domain.categories import CATEGORIES
from jalada.modules.ledger.domain.entries import (
    Correction,
    Entry,
    EntryStatus,
    counterparty_key,
    missing_fields,
)
from jalada.modules.ledger.domain.transactions import TransactionStatus, as_entry
from jalada.modules.ledger.domain.versions import still_current
from jalada.shared.errors import EntryNotFound, EvidenceNotFound, InvalidEntry
from jalada.unit_of_work import UnitOfWork


class EntryReview:
    """Confirming, correcting and hand-entering ledger entries. Every change is kept."""

    def __init__(self, unit_of_work: Callable[[], UnitOfWork], clock: Clock) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    def queue(self, user_id: UUID, limit: int = 100) -> list[ReviewItem]:
        with self._unit_of_work() as work:
            return review_queue(work, user_id, limit, self._clock.now())

    def confirm(
        self,
        user_id: UUID,
        entry_id: UUID,
        correction: Correction | None = None,
        based_on: int | None = None,
    ) -> Entry:
        """`based_on` is the version the edit was made from. When the entry has moved on
        since, nothing changes and ChangedElsewhere carries the current copy."""
        with self._unit_of_work() as work:
            payment = work.transactions_for(user_id).get(entry_id)
            if payment is not None:
                still_current(payment.version, based_on, lambda: as_entry(payment))
                if payment.status == TransactionStatus.CONFIRMED and correction is None:
                    return as_entry(payment)
                done = payment_review.confirm(
                    work, payment, correction or Correction(), self._clock.now()
                )
                # Read back for the version the save gave it.
                saved = work.transactions_for(user_id).get(entry_id) or done
                work.commit()
                return as_entry(saved)
            confirmed = self._confirm_certificate(work, user_id, entry_id, correction, based_on)
            work.commit()
        return confirmed

    def confirm_all(self, user_id: UUID, entry_ids: Sequence[UUID]) -> list[Entry]:
        """Confirms the listed payments that are ready to confirm, and skips the rest."""
        with self._unit_of_work() as work:
            done = confirm_all.confirm_all(work, user_id, entry_ids, self._clock.now())
            work.commit()
        return [as_entry(payment) for payment in done]

    def enter_by_hand(self, user_id: UUID, evidence_id: UUID, values: Correction) -> Entry:
        """For evidence nothing could read: the user types the payment in."""
        with self._unit_of_work() as work:
            evidence = work.evidence_for(user_id).get(evidence_id)
            if evidence is None:
                raise EvidenceNotFound
            if work.transactions_for(user_id).for_evidence(evidence_id) or work.entries_for(
                user_id
            ).for_evidence(evidence_id):
                raise InvalidEntry("This evidence already has an entry.")
            payment = payment_review.enter(work, evidence, values, self._clock.now())
            work.commit()
        return as_entry(payment)

    def mark_not_a_transaction(self, user_id: UUID, evidence_id: UUID) -> None:
        """The evidence leaves the review queue. Its payment or certificate, if any, is kept
        as rejected."""
        with self._unit_of_work() as work:
            if work.evidence_for(user_id).get(evidence_id) is None:
                raise EvidenceNotFound
            payment = work.transactions_for(user_id).for_evidence(evidence_id)
            if payment is not None:
                payment_review.reject(work, payment, self._clock.now())
            else:
                self._reject_certificate(work, user_id, evidence_id)
            work.evidence_for(user_id).set_status(evidence_id, EvidenceStatus.NOT_A_TRANSACTION)
            work.commit()

    def put_back(self, user_id: UUID, evidence_id: UUID) -> None:
        """Takes back "Not a transaction": the evidence returns to the review queue."""
        with self._unit_of_work() as work:
            putting_back.put_back(work, user_id, evidence_id, self._clock.now())
            work.commit()

    def _confirm_certificate(
        self,
        work: UnitOfWork,
        user_id: UUID,
        entry_id: UUID,
        correction: Correction | None,
        based_on: int | None,
    ) -> Entry:
        entry = work.entries_for(user_id).get(entry_id)
        if entry is None:
            raise EntryNotFound
        still_current(entry.version, based_on, lambda: entry)
        if entry.status == EntryStatus.CONFIRMED and correction is None:
            return entry
        confirmed = self._confirmed(_corrected(entry, correction or Correction()))
        now = self._clock.now()
        work.entries_for(user_id).update(confirmed)
        work.entries_for(user_id).add_revision(entry, confirmed, now)
        changed = correction is not None and any(vars(correction).values())
        action = AuditAction.CORRECTED if changed else AuditAction.CONFIRMED
        history.record_entry(work, entry, confirmed, Actor.USER, action, now)
        self._learn(work, user_id, confirmed)
        work.evidence_for(user_id).set_status(entry.evidence_id, EvidenceStatus.CONFIRMED)
        return work.entries_for(user_id).get(entry_id) or confirmed

    def _reject_certificate(self, work: UnitOfWork, user_id: UUID, evidence_id: UUID) -> None:
        entry = work.entries_for(user_id).for_evidence(evidence_id)
        if entry and entry.status == EntryStatus.CONFIRMED:
            raise InvalidEntry("This is already in your ledger.")
        if entry and entry.status != EntryStatus.REJECTED:
            rejected = replace(entry, status=EntryStatus.REJECTED)
            now = self._clock.now()
            work.entries_for(user_id).update(rejected)
            work.entries_for(user_id).add_revision(entry, rejected, now)
            history.record_entry(work, entry, rejected, Actor.USER, AuditAction.REJECTED, now)

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
