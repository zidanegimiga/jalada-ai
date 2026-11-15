"""Answering a suggested match: yes, the receipt and the payment are the same purchase, or
no, they are not. Either answer is kept, so the question is never asked twice."""

from collections.abc import Callable
from dataclasses import replace
from datetime import datetime
from uuid import UUID

from jalada.core.ports import Clock
from jalada.modules.evidence.domain.evidence import EvidenceStatus
from jalada.modules.ledger.application import history
from jalada.modules.ledger.application.match_undo import undo_match
from jalada.modules.ledger.domain.audit import Actor, AuditAction
from jalada.modules.ledger.domain.entries import Entry
from jalada.modules.ledger.domain.joining import joined
from jalada.modules.ledger.domain.suggestions import MatchSuggestion, SuggestionStatus
from jalada.modules.ledger.domain.transactions import as_entry
from jalada.shared.errors import SuggestionNotFound
from jalada.unit_of_work import UnitOfWork


class MatchReview:
    def __init__(self, unit_of_work: Callable[[], UnitOfWork], clock: Clock) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    def accept(self, user_id: UUID, suggestion_id: UUID) -> Entry:
        """Moves the receipt onto the payment, and returns the payment."""
        now = self._clock.now()
        with self._unit_of_work() as work:
            suggestion = _open(work, user_id, suggestion_id)
            transactions = work.transactions_for(user_id)
            payment = transactions.get(suggestion.payment_id)
            candidate = transactions.get(suggestion.candidate_id)
            if payment is None or candidate is None:
                raise SuggestionNotFound
            paid, merged = joined(payment, candidate, now)
            transactions.update(paid)
            transactions.update(merged)
            history.record_transaction(work, payment, paid, Actor.USER, AuditAction.LINKED, now)
            history.record_transaction(work, candidate, merged, Actor.USER, AuditAction.MERGED, now)
            for link in candidate.evidence:
                work.evidence_for(user_id).set_status(link.evidence_id, EvidenceStatus.LINKED)
            _decide(work, suggestion, SuggestionStatus.ACCEPTED, now)
            _close_the_rest(work, suggestion, now)
            work.commit()
        return as_entry(paid)

    def undo(self, user_id: UUID, suggestion_id: UUID) -> Entry:
        """Takes back a yes. Returns the payment without the receipt."""
        with self._unit_of_work() as work:
            paid = undo_match(work, user_id, suggestion_id, self._clock.now())
            work.commit()
        return as_entry(paid)

    def decline(self, user_id: UUID, suggestion_id: UUID) -> None:
        now = self._clock.now()
        with self._unit_of_work() as work:
            suggestion = _open(work, user_id, suggestion_id)
            _decide(work, suggestion, SuggestionStatus.DECLINED, now)
            work.commit()


def _open(work: UnitOfWork, user_id: UUID, suggestion_id: UUID) -> MatchSuggestion:
    suggestion = work.suggestions_for(user_id).get(suggestion_id)
    if suggestion is None or suggestion.status != SuggestionStatus.OPEN:
        raise SuggestionNotFound
    return suggestion


def _decide(
    work: UnitOfWork, suggestion: MatchSuggestion, status: SuggestionStatus, now: datetime
) -> None:
    work.suggestions_for(suggestion.user_id).decide(
        replace(suggestion, status=status, decided_at=now)
    )


def _close_the_rest(work: UnitOfWork, accepted: MatchSuggestion, now: datetime) -> None:
    """The payment has its receipt and the receipt its payment, so every other open
    question about either one has no answer to give."""
    suggestions = work.suggestions_for(accepted.user_id)
    involved = suggestions.involving(accepted.payment_id) + suggestions.involving(
        accepted.candidate_id
    )
    for other in {s.id: s for s in involved}.values():
        if other.id != accepted.id and other.status == SuggestionStatus.OPEN:
            _decide(work, other, SuggestionStatus.CLOSED, now)
