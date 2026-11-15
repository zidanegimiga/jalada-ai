"""Confirm all: the payments the user saw listed as ready, confirmed in one step."""

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from jalada.modules.ledger.application import payment_review
from jalada.modules.ledger.domain.entries import Correction
from jalada.modules.ledger.domain.ready import ready_to_confirm
from jalada.modules.ledger.domain.transactions import Transaction
from jalada.unit_of_work import UnitOfWork


def confirm_all(
    work: UnitOfWork, user_id: UUID, payment_ids: Sequence[UUID], now: datetime
) -> list[Transaction]:
    """Confirms each listed payment that is still ready, and leaves the rest on To check.
    Only the ids the user saw are confirmed, so a payment that arrived after the list was
    shown waits for its own look."""
    transactions = work.transactions_for(user_id)
    asked = {s.payment_id for s in work.suggestions_for(user_id).open()}
    done = []
    for payment_id in dict.fromkeys(payment_ids):
        payment = transactions.get(payment_id)
        if payment and ready_to_confirm(payment, open_question=payment_id in asked):
            done.append(payment_review.confirm(work, payment, Correction(), now))
    return done
