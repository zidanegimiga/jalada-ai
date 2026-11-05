from datetime import date

from samples import CERTIFICATE, MPESA_SENT

from jalada.domain.categories import Purpose
from jalada.domain.evidence import EvidenceKind
from jalada.pipeline.classifier import Preference
from jalada.pipeline.process import Budget, run_pipeline

TODAY = date(2026, 11, 5)
KNOWN = {"jane wanjiku": Preference("personal_family_support", Purpose.PERSONAL, 3)}


def run(text: str | None, content_type: str = "text/plain", **kwargs: object):  # type: ignore[no-untyped-def]
    options = {"preferences": {}, "is_duplicate": lambda _: False, **kwargs}
    return run_pipeline(text, content_type, today=TODAY, budget=Budget(), **options)  # type: ignore[arg-type]


def test_a_known_counterparty_is_proposed_in_one_attempt() -> None:
    result = run(MPESA_SENT, preferences=KNOWN)

    assert result.outcome == "proposed"
    assert result.attempts == 1
    assert [step.step for step in result.steps] == ["detect", "extract", "classify", "verify"]


def test_a_certificate_is_proposed_as_consultancy_fees() -> None:
    result = run(CERTIFICATE, "application/pdf")

    assert result.outcome == "proposed"
    assert result.classification is not None
    assert result.classification.category == "consultancy_fees"


def test_an_unknown_counterparty_needs_review_with_the_fields_kept() -> None:
    result = run(MPESA_SENT)

    assert result.outcome == "needs_review"
    assert result.extraction is not None and result.extraction.amount_cents == 15000


def test_rules_are_not_retried_when_the_fields_are_wrong() -> None:
    result = run(MPESA_SENT.replace("5/11/26", "5/12/26"), preferences=KNOWN)

    assert result.outcome == "needs_review"
    assert result.attempts == 1
    assert result.verdict is not None and result.verdict.problems == ["date is in the future"]


def test_a_photo_without_text_needs_review() -> None:
    result = run(None, "image/jpeg")

    assert result.kind == EvidenceKind.UNKNOWN
    assert result.extraction is None
    assert result.outcome == "needs_review"


def test_a_duplicate_is_reported() -> None:
    assert run(MPESA_SENT, is_duplicate=lambda _: True).outcome == "duplicate"


def test_step_records_hold_fields_but_never_the_raw_text() -> None:
    result = run(MPESA_SENT, preferences=KNOWN)

    recorded = repr([step.input for step in result.steps])
    assert "Confirmed" not in recorded
    assert result.steps[0].input == {"content_type": "text/plain", "text_length": len(MPESA_SENT)}
    assert all(step.duration_ms >= 0 for step in result.steps)
