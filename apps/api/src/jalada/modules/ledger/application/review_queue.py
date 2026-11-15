"""What is waiting for the user on To check, oldest first: questions about suggested
matches and receipts with no payment, payments and certificates to confirm, and evidence
nothing could read."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from jalada.modules.evidence.domain.evidence import Evidence
from jalada.modules.ledger.domain.entries import Entry, EntryKind
from jalada.modules.ledger.domain.how_paid import DEFAULT_ASKING, time_to_ask
from jalada.modules.ledger.domain.suggestions import MatchSuggestion
from jalada.modules.ledger.domain.transactions import (
    Transaction,
    as_entry,
    candidate_as_entry,
)
from jalada.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class SuggestedMatch:
    """A receipt that may belong to the payment it is shown with."""

    suggestion: MatchSuggestion
    receipt: Evidence
    # The receipt as it was read: amount, name and date.
    candidate: Transaction


@dataclass(frozen=True)
class ReviewItem:
    """One thing waiting for the user: an entry to check, or evidence with no entry yet."""

    evidence: Evidence
    entry: Entry | None
    # True when the category is a model's suggestion, not the user's own or a rule's.
    category_suggested: bool = False
    # Set when the question is whether a receipt belongs to this payment.
    match: SuggestedMatch | None = None
    # True when the entry is a receipt whose payment never arrived: was it cash or card?
    ask_how_paid: bool = False


def review_queue(work: UnitOfWork, user_id: UUID, limit: int, now: datetime) -> list[ReviewItem]:
    questions = _questions(work, user_id)
    waiting = _how_paid(work, user_id, limit, now)
    asked = {item.entry.id for item in questions if item.entry}
    # A payment with an open question is shown as the question, and comes back once answered.
    payments = [p for p in work.transactions_for(user_id).pending(limit) if p.id not in asked]
    certificates = work.entries_for(user_id).pending(limit, EntryKind.WITHHOLDING_CERTIFICATE)
    evidence = work.evidence_for(user_id)
    items = [*questions, *waiting]
    items += [item for p in payments if (item := _payment_item(work, p))]
    items += [
        ReviewItem(e, entry) for entry in certificates if (e := evidence.get(entry.evidence_id))
    ]
    items += [ReviewItem(e, None) for e in evidence.needing_entry(limit)]
    return sorted(items, key=lambda item: item.evidence.received_at)[:limit]


def _payment_item(
    work: UnitOfWork, payment: Transaction, match: SuggestedMatch | None = None
) -> ReviewItem | None:
    evidence = work.evidence_for(payment.user_id).get(payment.evidence[0].evidence_id)
    if evidence is None:
        return None
    suggested = any(line.suggested for line in payment.lines)
    return ReviewItem(evidence, as_entry(payment), suggested, match)


def _questions(work: UnitOfWork, user_id: UUID) -> list[ReviewItem]:
    items = []
    transactions, evidence = work.transactions_for(user_id), work.evidence_for(user_id)
    for suggestion in work.suggestions_for(user_id).open():
        payment = transactions.get(suggestion.payment_id)
        candidate = transactions.get(suggestion.candidate_id)
        receipt = evidence.get(candidate.evidence[0].evidence_id) if candidate else None
        if payment is None or candidate is None or receipt is None:
            continue
        match = SuggestedMatch(suggestion, receipt, candidate)
        if item := _payment_item(work, payment, match):
            items.append(item)
    return items


def _how_paid(work: UnitOfWork, user_id: UUID, limit: int, now: datetime) -> list[ReviewItem]:
    """Receipts that waited long enough for a payment, with nothing offered for them."""
    asked = {s.candidate_id for s in work.suggestions_for(user_id).open()}
    evidence = work.evidence_for(user_id)
    oldest = now - DEFAULT_ASKING.wait
    return [
        ReviewItem(receipt, candidate_as_entry(candidate), ask_how_paid=True)
        for candidate in work.transactions_for(user_id).candidates(oldest, limit)
        if time_to_ask(candidate, now, candidate.id in asked)
        and (receipt := evidence.get(candidate.evidence[0].evidence_id))
    ]
