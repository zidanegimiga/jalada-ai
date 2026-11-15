"""Whether a receipt waiting as a candidate may be the same purchase as a payment.

The amount must be the same, and at least one more sign must agree: a date within a few
days or a similar name. The bar is low on purpose, because the user answers every
suggestion and wrongly joining two payments is worse than asking one question. A category
is never a sign: two purchases can share one (design 03, "Matching")."""

import re
from collections.abc import Callable
from dataclasses import dataclass
from difflib import SequenceMatcher

from jalada.modules.ledger.domain.transactions import (
    EvidenceRole,
    Transaction,
    TransactionKind,
    TransactionStatus,
)


@dataclass(frozen=True)
class MatchRules:
    # The most days a receipt and its payment can be apart.
    days_apart: int = 3
    # How alike two names must be, from 0 to 1, when they share no word.
    name_likeness: float = 0.6


@dataclass(frozen=True)
class Sign:
    points: float
    reason: str


DEFAULT_RULES = MatchRules()
# Points for the amount, which every suggestion needs.
SAME_AMOUNT = Sign(0.5, "same amount")
PAYMENTS = (TransactionStatus.PROPOSED, TransactionStatus.NEEDS_REVIEW, TransactionStatus.CONFIRMED)
# Words that say what kind of business it is, not which one.
COMMON_WORDS = {"ltd", "limited", "co", "company", "the", "and", "kenya", "enterprises"}
TILL_NUMBER = re.compile(r"\d{5,}")


def same_purchase(
    candidate: Transaction, payment: Transaction, rules: MatchRules = DEFAULT_RULES
) -> tuple[float, tuple[str, ...]] | None:
    """The score and reasons when the two may be one purchase, or None when they cannot be."""
    if not _can_pair(candidate, payment):
        return None
    if candidate.amount_cents is None or candidate.amount_cents != payment.amount_cents:
        return None
    if _too_far_apart(candidate, payment, rules):
        return None
    signs = [sign for check in SIGNS if (sign := check(candidate, payment, rules))]
    if not signs:
        return None
    agreed = [SAME_AMOUNT, *signs]
    return round(sum(s.points for s in agreed), 2), tuple(s.reason for s in agreed)


def _can_pair(candidate: Transaction, payment: Transaction) -> bool:
    has_receipt = any(link.role == EvidenceRole.RECEIPT for link in payment.evidence)
    return (
        candidate.status == TransactionStatus.CANDIDATE
        and payment.status in PAYMENTS
        and payment.kind == TransactionKind.PAYMENT
        and payment.direction is not None
        and candidate.direction == payment.direction
        and not has_receipt
    )


def _too_far_apart(candidate: Transaction, payment: Transaction, rules: MatchRules) -> bool:
    days = _days_apart(candidate, payment)
    return days is not None and days > rules.days_apart


def _days_apart(candidate: Transaction, payment: Transaction) -> int | None:
    if candidate.occurred_on is None or payment.occurred_on is None:
        return None
    return abs((candidate.occurred_on - payment.occurred_on).days)


def _close_dates(candidate: Transaction, payment: Transaction, rules: MatchRules) -> Sign | None:
    days = _days_apart(candidate, payment)
    if days is None:
        return None
    if days == 0:
        return Sign(0.3, "same day")
    return Sign(0.2, "1 day apart" if days == 1 else f"{days} days apart")


def _similar_names(candidate: Transaction, payment: Transaction, rules: MatchRules) -> Sign | None:
    if not candidate.counterparty or not payment.counterparty:
        return None
    if names_alike(candidate.counterparty, payment.counterparty, rules.name_likeness):
        return Sign(0.2, "similar name")
    return None


def names_alike(first: str, second: str, likeness: float) -> bool:
    """True when the names share a word or a till number, or are spelt much the same."""
    if set(TILL_NUMBER.findall(first)) & set(TILL_NUMBER.findall(second)):
        return True
    words = [_words(first), _words(second)]
    if words[0] & words[1]:
        return True
    first_joined, second_joined = (" ".join(sorted(w)) for w in words)
    if not first_joined or not second_joined:
        return False
    return SequenceMatcher(None, first_joined, second_joined).ratio() >= likeness


def _words(name: str) -> set[str]:
    found = re.findall(r"[a-z]+", name.lower())
    return {word for word in found if len(word) >= 3 and word not in COMMON_WORDS}


SIGNS: tuple[Callable[[Transaction, Transaction, MatchRules], Sign | None], ...] = (
    _close_dates,
    _similar_names,
)
