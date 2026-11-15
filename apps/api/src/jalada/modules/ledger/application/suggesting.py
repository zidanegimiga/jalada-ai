"""Offering suggested matches when a receipt or a payment is saved."""

import uuid
from datetime import datetime

from jalada.modules.ledger.domain.same_purchase import same_purchase
from jalada.modules.ledger.domain.suggestions import (
    MatchSuggestion,
    SuggestionKind,
    SuggestionStatus,
)
from jalada.modules.ledger.domain.transactions import Transaction, TransactionStatus
from jalada.unit_of_work import UnitOfWork


def suggest_same_purchase(
    work: UnitOfWork, saved: Transaction, now: datetime
) -> list[MatchSuggestion]:
    """Offers every pair the saved receipt or payment may make with what is already
    recorded, and returns the new suggestions. A pair offered before, whatever the user
    answered, is not offered again. Nothing is linked here: the user decides."""
    if saved.amount_cents is None:
        return []
    user_id = saved.user_id
    asked = {
        (s.payment_id, s.candidate_id) for s in work.suggestions_for(user_id).involving(saved.id)
    }
    offered = []
    for other in work.transactions_for(user_id).with_amount(saved.amount_cents):
        is_candidate = saved.status == TransactionStatus.CANDIDATE
        candidate, payment = (saved, other) if is_candidate else (other, saved)
        scored = same_purchase(candidate, payment)
        if scored is None or (payment.id, candidate.id) in asked:
            continue
        score, reasons = scored
        suggestion = MatchSuggestion(
            id=uuid.uuid4(),
            user_id=user_id,
            kind=SuggestionKind.SAME_PURCHASE,
            payment_id=payment.id,
            candidate_id=candidate.id,
            score=score,
            reasons=reasons,
            status=SuggestionStatus.OPEN,
            created_at=now,
        )
        work.suggestions_for(user_id).add(suggestion)
        offered.append(suggestion)
    return offered
