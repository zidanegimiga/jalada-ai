import time
from collections.abc import Callable
from datetime import date
from typing import Any

from jalada.modules.evidence.domain.evidence import EvidenceKind
from jalada.modules.ledger.domain.categories import Purpose
from jalada.modules.pipeline.domain.classifier import Preference, classify
from jalada.modules.pipeline.domain.detector import detect
from jalada.modules.pipeline.domain.extraction import Classification, Extraction
from jalada.modules.pipeline.domain.extractor import extract_with_rules
from jalada.modules.pipeline.domain.model import (
    LanguageModel,
    ModelFailed,
    ModelReply,
    ModelUsage,
)
from jalada.modules.pipeline.domain.model_steps import classify_with_model, extract_with_model
from jalada.modules.pipeline.domain.run_types import (
    Budget,
    EvidenceInput,
    PipelineResult,
    StepRecord,
)
from jalada.modules.pipeline.domain.verifier import verify


def run_pipeline(
    evidence: EvidenceInput,
    preferences: dict[str, Preference],
    is_duplicate: Callable[[Extraction], bool],
    today: date,
    budget: Budget,
    model: LanguageModel | None = None,
) -> PipelineResult:
    """One piece of evidence through detect, extract, classify and verify.

    Rules go first; the model is used only when rules cannot cope and the budget allows.
    Stops when the verifier passes, the budget runs out, or the verifier fails twice.
    Anything that does not pass ends as needs_review, for the user to decide.
    """
    run = _Run(PipelineResult(), budget, model)
    run.result.kind = detect(evidence.text, evidence.content_type)
    run.record(
        "detect",
        1,
        {"content_type": evidence.content_type, "text_length": len(evidence.text or "")},
        {"kind": run.result.kind},
        "ok",
    )
    feedback: list[str] = []
    for attempt in range(1, budget.max_attempts + 1):
        run.result.attempts = attempt
        extraction, method, sureness = run.extract(evidence, attempt, feedback)
        if extraction is None:
            break
        if run.result.kind == EvidenceKind.UNKNOWN:
            run.result.kind = extraction.kind
        classification = run.classify(extraction, preferences, attempt)
        verdict = verify(extraction, classification, today, is_duplicate(extraction), sureness)
        run.record(
            "verify",
            attempt,
            {},
            {"problems": verdict.problems, "review_reasons": verdict.review_reasons},
            "pass" if verdict.passed else "fail",
        )
        run.result.extraction, run.result.classification = extraction, classification
        run.result.verdict = verdict
        if verdict.duplicate or verdict.passed:
            run.result.outcome = "duplicate" if verdict.duplicate else "proposed"
            break
        # Reaching here means the verifier failed. Rules give the same answer every time,
        # so only model extractions are retried, with the problems as feedback.
        if attempt >= 2 or method == "rules" or not verdict.problems:
            break
        feedback = verdict.problems
    return run.result


class _Run:
    """Keeps the result, the model spend and the step records for one pipeline run."""

    def __init__(self, result: PipelineResult, budget: Budget, model: LanguageModel | None):
        self.result = result
        self._budget = budget
        self._model = model
        self._clock = time.perf_counter()

    def extract(
        self, evidence: EvidenceInput, attempt: int, feedback: list[str]
    ) -> tuple[Extraction | None, str, float]:
        if attempt == 1:
            extraction = extract_with_rules(self.result.kind, evidence.text)
            self.record(
                "extract",
                attempt,
                {"kind": self.result.kind, "method": "rules"},
                _fields(extraction),
                "ok" if extraction else "nothing",
            )
            if extraction:
                return extraction, "rules", 1.0
        model = self._usable_model()
        if model is None:
            return None, "rules" if attempt == 1 else "model", 1.0
        try:
            extraction, sureness, reply = extract_with_model(
                model, evidence.text, evidence.image, feedback
            )
        except ModelFailed as failed:
            # The summary names models and failure kinds only, never content.
            given = {"method": "model", "failures": str(failed)}
            self.record("extract", attempt, given, {}, "model failed")
            return None, "model", 0.0
        self._spend(reply.usage)
        self.record(
            "extract",
            attempt,
            {
                "method": "model",
                **_model_call(model, reply),
                "photo": evidence.text is None,
                "feedback": feedback,
            },
            {**_fields(extraction), "confidence": sureness},
            "ok" if extraction else "nothing",
        )
        return extraction, "model", sureness

    def classify(
        self, extraction: Extraction, preferences: dict[str, Preference], attempt: int
    ) -> Classification:
        classification = classify(extraction, preferences)
        call: dict[str, Any] = {}
        if classification.purpose == Purpose.UNSURE and classification.category is None:
            classification, call = self._classify_with_model(extraction, classification)
        self.record(
            "classify",
            attempt,
            {"source": classification.source, **call},
            {
                "purpose": classification.purpose,
                "category": classification.category,
                "confidence": classification.confidence,
            },
            "ok",
        )
        return classification

    def _classify_with_model(
        self, extraction: Extraction, fallback: Classification
    ) -> tuple[Classification, dict[str, Any]]:
        """The model's classification, and what to record about the call."""
        model = self._usable_model()
        if model is None:
            return fallback, {}
        try:
            classification, reply = classify_with_model(model, extraction)
        except ModelFailed as failed:
            return fallback, {"failures": str(failed)}
        self._spend(reply.usage)
        return classification, _model_call(model, reply)

    def _usable_model(self) -> LanguageModel | None:
        """The model, if there is one and the budget still allows a call."""
        return self._model if self._budget.allows(self.result.usage) else None

    def _spend(self, usage: ModelUsage) -> None:
        self.result.usage = self.result.usage + usage

    def record(
        self, step: str, attempt: int, given: dict[str, Any], output: dict[str, Any], verdict: str
    ) -> None:
        now = time.perf_counter()
        duration = int((now - self._clock) * 1000)
        self._clock = now
        self.result.steps.append(StepRecord(step, attempt, given, output, verdict, duration))


def _model_call(model: LanguageModel, reply: ModelReply) -> dict[str, Any]:
    """Which model answered, every attempt including failed ones, and the tokens used."""
    return {
        "model": reply.answered_by or model.name,
        "attempts": list(reply.attempts),
        "input_tokens": reply.usage.input_tokens,
        "output_tokens": reply.usage.output_tokens,
    }


def _fields(extraction: Extraction | None) -> dict[str, Any]:
    return extraction.to_record() if extraction else {}
