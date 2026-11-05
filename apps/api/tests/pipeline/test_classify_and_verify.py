from dataclasses import replace
from datetime import date

import pytest
from samples import CERTIFICATE, MPESA_SENT

from jalada.domain.categories import Purpose
from jalada.domain.extraction import Classification, Extraction
from jalada.pipeline.certificates import parse_certificate
from jalada.pipeline.classifier import Preference, classify
from jalada.pipeline.mpesa import parse_mpesa
from jalada.pipeline.verifier import verify

TODAY = date(2026, 11, 5)
SURE = Classification(Purpose.PERSONAL, "personal_food", 0.95, "preference")


def parsed(extraction: Extraction | None) -> Extraction:
    assert extraction is not None
    return extraction


sent = parsed(parse_mpesa(MPESA_SENT))
certificate = parsed(parse_certificate(CERTIFICATE))


@pytest.mark.parametrize(("times_used", "confidence"), [(1, 0.85), (2, 0.95), (7, 0.95)])
def test_the_users_own_past_choice_comes_first(times_used: int, confidence: float) -> None:
    preferences = {
        "jane wanjiku": Preference("personal_family_support", Purpose.PERSONAL, times_used)
    }

    result = classify(sent, preferences)

    assert (result.category, result.purpose) == ("personal_family_support", Purpose.PERSONAL)
    assert result.confidence == confidence
    assert result.source == "preference"


def test_an_unknown_counterparty_is_unsure() -> None:
    result = classify(sent, {})

    assert result.purpose == Purpose.UNSURE
    assert result.category is None
    assert result.confidence == 0


def test_consultancy_certificates_are_consultancy_fees() -> None:
    result = classify(certificate, {})

    assert (result.category, result.purpose, result.source) == (
        "consultancy_fees",
        Purpose.BUSINESS,
        "rule",
    )


def test_a_complete_confident_extraction_passes() -> None:
    assert verify(sent, SURE, TODAY, is_duplicate=False).passed


def test_low_confidence_goes_to_review_without_calling_the_fields_wrong() -> None:
    verdict = verify(sent, classify(sent, {}), TODAY, is_duplicate=False)

    assert not verdict.passed
    assert verdict.problems == []
    assert verdict.review_reasons == ["purpose not certain"]


def test_duplicates_are_flagged() -> None:
    verdict = verify(sent, SURE, TODAY, is_duplicate=True)

    assert verdict.duplicate and not verdict.passed


@pytest.mark.parametrize(
    ("change", "problem"),
    [
        ({"amount_cents": None}, "no amount"),
        ({"amount_cents": 0}, "no amount"),
        ({"occurred_on": None}, "no date"),
        ({"occurred_on": date(2026, 11, 6)}, "date is in the future"),
        ({"occurred_on": date(2018, 1, 1)}, "date is more than seven years ago"),
        ({"direction": None}, "no direction"),
    ],
)
def test_broken_fields_are_rejected(change: dict[str, object], problem: str) -> None:
    verdict = verify(replace(sent, **change), SURE, TODAY, is_duplicate=False)  # type: ignore[arg-type]

    assert problem in verdict.problems


def test_certificate_tax_must_equal_gross_times_rate() -> None:
    wrong = replace(certificate, tax_withheld_cents=210000)

    verdict = verify(wrong, SURE, TODAY, is_duplicate=False)

    assert verdict.problems == ["tax withheld does not match gross amount times rate"]
    assert verify(certificate, SURE, TODAY, is_duplicate=False).passed
