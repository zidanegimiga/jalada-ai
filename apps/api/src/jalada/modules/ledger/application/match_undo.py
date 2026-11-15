"""Taking back "Yes, same purchase": the receipt waits for its payment again, and the pair
is not offered again. The audit trail keeps both the match and its undoing."""

from dataclasses import replace
from datetime import datetime
from typing import Any
from uuid import UUID

from jalada.modules.evidence.domain.evidence import EvidenceStatus
from jalada.modules.ledger.application import history
from jalada.modules.ledger.domain.audit import Actor, AuditAction, snapshot
from jalada.modules.ledger.domain.categories import Purpose
from jalada.modules.ledger.domain.joining import separated
from jalada.modules.ledger.domain.suggestions import MatchSuggestion, SuggestionStatus
from jalada.modules.ledger.domain.transactions import Transaction, TransactionLine
from jalada.shared.errors import SuggestionNotFound
from jalada.unit_of_work import UnitOfWork


def undo_match(work: UnitOfWork, user_id: UUID, suggestion_id: UUID, now: datetime) -> Transaction:
    """Returns the payment as it is after the receipt is taken off it."""
    suggestion = work.suggestions_for(user_id).get(suggestion_id)
    if suggestion is None or suggestion.status != SuggestionStatus.ACCEPTED:
        raise SuggestionNotFound
    transactions = work.transactions_for(user_id)
    payment = transactions.get(suggestion.payment_id)
    candidate = transactions.get(suggestion.candidate_id)
    if payment is None or candidate is None:
        raise SuggestionNotFound
    paid, waiting = separated(payment, candidate, _lines_before(work, payment))
    transactions.update(paid)
    for link in candidate.evidence:
        transactions.unlink(payment.id, link.evidence_id)
        work.evidence_for(user_id).set_status(link.evidence_id, EvidenceStatus.CANDIDATE)
    transactions.update(waiting)
    history.record_transaction(work, payment, paid, Actor.USER, AuditAction.UNLINKED, now)
    history.record_transaction(work, candidate, waiting, Actor.USER, AuditAction.UNLINKED, now)
    _reopen_the_rest(work, suggestion)
    work.suggestions_for(user_id).decide(
        replace(suggestion, status=SuggestionStatus.DECLINED, decided_at=now)
    )
    return paid


def _lines_before(work: UnitOfWork, payment: Transaction) -> tuple[TransactionLine, ...] | None:
    """The payment's lines from before the receipt joined it, when they have not changed
    since. None when they have, so the user's own choice stays."""
    joins = [
        e
        for e in work.audit_for(payment.user_id).for_subject(payment.id)
        if e.action == AuditAction.LINKED and e.actor == Actor.USER
    ]
    if not joins or not joins[-1].before or not joins[-1].after:
        return None
    if snapshot(payment)["lines"] != joins[-1].after["lines"]:
        return None
    return tuple(_line(saved) for saved in joins[-1].before["lines"])


def _line(saved: dict[str, Any]) -> TransactionLine:
    return TransactionLine(
        saved["amount_cents"],
        saved["category"],
        Purpose(saved["purpose"]),
        bool(saved.get("suggested", False)),
    )


def _reopen_the_rest(work: UnitOfWork, undone: MatchSuggestion) -> None:
    """Questions closed when the match was made can be asked again."""
    suggestions = work.suggestions_for(undone.user_id)
    involved = suggestions.involving(undone.payment_id) + suggestions.involving(undone.candidate_id)
    for other in {s.id: s for s in involved}.values():
        closed_with_it = other.status == SuggestionStatus.CLOSED
        if closed_with_it and other.decided_at == undone.decided_at:
            suggestions.decide(replace(other, status=SuggestionStatus.OPEN, decided_at=None))
