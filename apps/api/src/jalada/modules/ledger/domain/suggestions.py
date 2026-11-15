"""Suggested matches: two records that may describe the same money. A suggestion is only
ever offered to the user, never applied without them (design 03, "Matching")."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class SuggestionKind(StrEnum):
    # A receipt waiting as a candidate, and a payment that may be the same purchase.
    SAME_PURCHASE = "same_purchase"


class SuggestionStatus(StrEnum):
    OPEN = "open"
    ACCEPTED = "accepted"
    # Kept, so the same pair is never offered again.
    DECLINED = "declined"
    # No longer possible: one side was matched to something else.
    CLOSED = "closed"


@dataclass(frozen=True)
class MatchSuggestion:
    id: UUID
    user_id: UUID
    kind: SuggestionKind
    payment_id: UUID
    candidate_id: UUID
    # From 0 to 1. Higher means more signs that the two are the same.
    score: float
    # What the two have in common, such as "same amount" and "same day".
    reasons: tuple[str, ...]
    status: SuggestionStatus
    created_at: datetime
    decided_at: datetime | None = None
