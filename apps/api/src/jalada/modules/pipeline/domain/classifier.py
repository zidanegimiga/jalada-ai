from collections.abc import Sequence
from dataclasses import dataclass

from jalada.modules.evidence.domain.evidence import EvidenceKind
from jalada.modules.ledger.domain.categories import CATEGORIES, Purpose
from jalada.modules.ledger.domain.entries import counterparty_key
from jalada.modules.ledger.domain.transfers import OWN_TRANSFER_OUT, paybill
from jalada.modules.pipeline.domain.extraction import Classification, Extraction


@dataclass(frozen=True)
class Preference:
    """A user's earlier choice for a counterparty."""

    category: str
    purpose: Purpose
    times_used: int


UNSURE = Classification(Purpose.UNSURE, None, 0.0, "none")
CONSULTANCY_WORDS = ("consultancy", "professional", "management", "training")


def classify(
    extraction: Extraction,
    preferences: dict[str, Preference],
    own_accounts: Sequence[dict[str, str]] = (),
) -> Classification:
    """A transfer to an account the user said is theirs first, then the user's own past
    choice, then shared rules. Never decides what is taxable. `own_accounts` holds how
    messages name each of the user's accounts."""
    sent_to = paybill(extraction.direction, extraction.counterparty, extraction.reference)
    if sent_to and sent_to in own_accounts:
        return Classification(Purpose.PERSONAL, OWN_TRANSFER_OUT, 0.95, "own_account")
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
