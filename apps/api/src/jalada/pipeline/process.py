import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from jalada.domain.evidence import EvidenceKind
from jalada.domain.extraction import Classification, Extraction
from jalada.pipeline.classifier import Preference, classify
from jalada.pipeline.detector import detect
from jalada.pipeline.extractor import extract_with_rules
from jalada.pipeline.verifier import Verdict, verify


@dataclass(frozen=True)
class Budget:
    max_attempts: int = 3


@dataclass(frozen=True)
class StepRecord:
    step: str
    attempt: int
    input: dict[str, Any]
    output: dict[str, Any]
    verdict: str
    duration_ms: int


@dataclass
class PipelineResult:
    kind: EvidenceKind = EvidenceKind.UNKNOWN
    extraction: Extraction | None = None
    classification: Classification | None = None
    verdict: Verdict | None = None
    # proposed, needs_review or duplicate
    outcome: str = "needs_review"
    attempts: int = 0
    steps: list[StepRecord] = field(default_factory=list)


def run_pipeline(
    text: str | None,
    content_type: str,
    preferences: dict[str, Preference],
    is_duplicate: Callable[[Extraction], bool],
    today: date,
    budget: Budget,
) -> PipelineResult:
    """One piece of evidence through detect, extract, classify and verify.

    Stops when the verifier passes, the budget runs out, or the verifier fails twice.
    Anything that does not pass ends as needs_review, for the user to decide.
    """
    result = PipelineResult()
    record = _recorder(result)
    result.kind = detect(text, content_type)
    record(
        "detect",
        1,
        {"content_type": content_type, "text_length": len(text or "")},
        {"kind": result.kind},
        "ok",
    )
    for attempt in range(1, budget.max_attempts + 1):
        result.attempts = attempt
        extraction = extract_with_rules(result.kind, text)
        method = "rules"
        record(
            "extract",
            attempt,
            {"kind": result.kind, "method": method},
            extraction.to_record() if extraction else {},
            "ok" if extraction else "nothing",
        )
        if extraction is None:
            break
        classification = classify(extraction, preferences)
        record(
            "classify",
            attempt,
            {"counterparty_known": classification.source == "preference"},
            {
                "purpose": classification.purpose,
                "category": classification.category,
                "confidence": classification.confidence,
                "source": classification.source,
            },
            "ok",
        )
        verdict = verify(extraction, classification, today, is_duplicate(extraction))
        record(
            "verify",
            attempt,
            {},
            {"problems": verdict.problems, "review_reasons": verdict.review_reasons},
            "pass" if verdict.passed else "fail",
        )
        result.extraction, result.classification, result.verdict = (
            extraction,
            classification,
            verdict,
        )
        if verdict.duplicate:
            result.outcome = "duplicate"
            break
        if verdict.passed:
            result.outcome = "proposed"
            break
        # Reaching here means the verifier failed on this attempt. Stop after two failures.
        # Rules give the same answer every time, so only model extractions are retried.
        if attempt >= 2 or method == "rules" or not verdict.problems:
            break
    return result


def _recorder(result: PipelineResult) -> Callable[..., None]:
    started = time.perf_counter()

    def record(
        step: str, attempt: int, given: dict[str, Any], output: dict[str, Any], verdict: str
    ) -> None:
        nonlocal started
        now = time.perf_counter()
        duration = int((now - started) * 1000)
        started = now
        result.steps.append(StepRecord(step, attempt, given, output, verdict, duration))

    return record
