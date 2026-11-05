from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal

from jalada.domain.evidence import EvidenceKind
from jalada.domain.extraction import Classification, Extraction

CONFIDENCE_THRESHOLD = 0.8
OLDEST_ACCEPTED = timedelta(days=7 * 366)


@dataclass(frozen=True)
class Verdict:
    passed: bool
    # Problems that mean the extraction is wrong or a duplicate.
    problems: list[str] = field(default_factory=list)
    # Reasons a correct extraction still needs the user to look.
    review_reasons: list[str] = field(default_factory=list)
    duplicate: bool = False


def verify(
    extraction: Extraction,
    classification: Classification,
    today: date,
    is_duplicate: bool,
    extraction_confidence: float = 1.0,
) -> Verdict:
    """`extraction_confidence` is 1 for rules, and the model's own score for model answers."""
    problems = _field_problems(extraction, today)
    if is_duplicate:
        return Verdict(False, ["already recorded"], duplicate=True)
    review = []
    if extraction_confidence < CONFIDENCE_THRESHOLD:
        review.append("amount or date not certain")
    if classification.confidence < CONFIDENCE_THRESHOLD:
        review.append("purpose not certain")
    return Verdict(not problems and not review, problems, review)


def _field_problems(extraction: Extraction, today: date) -> list[str]:
    problems = []
    if not extraction.amount_cents or extraction.amount_cents <= 0:
        problems.append("no amount")
    if extraction.occurred_on is None:
        problems.append("no date")
    elif extraction.occurred_on > today:
        problems.append("date is in the future")
    elif extraction.occurred_on < today - OLDEST_ACCEPTED:
        problems.append("date is more than seven years ago")
    if extraction.direction is None:
        problems.append("no direction")
    if extraction.kind == EvidenceKind.WITHHOLDING_CERTIFICATE:
        problems += _certificate_problems(extraction)
    return problems


def _certificate_problems(extraction: Extraction) -> list[str]:
    if not extraction.certificate_serial:
        return ["no certificate serial"]
    if extraction.amount_cents is None or extraction.tax_withheld_cents is None:
        return ["no tax amounts"]
    rate = Decimal(extraction.tax_rate_percent or "0")
    expected = Decimal(extraction.amount_cents) * rate / 100
    if abs(expected - extraction.tax_withheld_cents) > 1:
        return ["tax withheld does not match gross amount times rate"]
    return []
