from dataclasses import dataclass

from jalada.domain.categories import CATEGORIES, Purpose
from jalada.domain.entries import counterparty_key
from jalada.domain.evidence import EvidenceKind
from jalada.domain.extraction import Classification, Extraction


@dataclass(frozen=True)
class Preference:
    """A user's earlier choice for a counterparty."""

    category: str
    purpose: Purpose
    times_used: int


UNSURE = Classification(Purpose.UNSURE, None, 0.0, "none")
CONSULTANCY_WORDS = ("consultancy", "professional", "management", "training")


def classify(extraction: Extraction, preferences: dict[str, Preference]) -> Classification:
    """The user's own past choice first, then shared rules. Never decides what is taxable."""
    if extraction.counterparty:
        preference = preferences.get(counterparty_key(extraction.counterparty))
        if preference and preference.category in CATEGORIES:
            confidence = 0.95 if preference.times_used >= 2 else 0.85
            return Classification(preference.purpose, preference.category, confidence, "preference")
    return _by_rule(extraction)


def _by_rule(extraction: Extraction) -> Classification:
    if extraction.kind == EvidenceKind.WITHHOLDING_CERTIFICATE:
        nature = (extraction.nature or "").lower()
        if any(word in nature for word in CONSULTANCY_WORDS):
            return Classification(Purpose.BUSINESS, "consultancy_fees", 0.9, "rule")
    return UNSURE
