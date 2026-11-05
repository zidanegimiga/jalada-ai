import time
from collections.abc import Callable
from datetime import date
from typing import Any

from jalada.domain.categories import Purpose
from jalada.domain.evidence import EvidenceKind
from jalada.domain.extraction import Classification, Extraction
from jalada.pipeline.classifier import Preference, classify
from jalada.pipeline.detector import detect
from jalada.pipeline.extractor import extract_with_rules
from jalada.pipeline.model import LanguageModel, ModelFailed, ModelUsage
from jalada.pipeline.model_steps import classify_with_model, extract_with_model
from jalada.pipeline.run_types import Budget, EvidenceInput, PipelineResult, StepRecord
from jalada.pipeline.verifier import verify


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
            extraction, sureness, usage = extract_with_model(
                model, evidence.text, evidence.image, feedback
            )
        except ModelFailed:
            self.record("extract", attempt, {"method": "model"}, {}, "model failed")
            return None, "model", 0.0
        self._spend(usage)
        self.record(
            "extract",
            attempt,
            {
                "method": "model",
                "model": model.name,
                "photo": evidence.text is None,
                "feedback": feedback,
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
            },
            {**_fields(extraction), "confidence": sureness},
            "ok" if extraction else "nothing",
        )
        return extraction, "model", sureness

    def classify(
        self, extraction: Extraction, preferences: dict[str, Preference], attempt: int
    ) -> Classification:
        classification = classify(extraction, preferences)
        if classification.purpose == Purpose.UNSURE and classification.category is None:
            classification = self._classify_with_model(extraction, classification)
        self.record(
            "classify",
            attempt,
            {"source": classification.source},
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
    ) -> Classification:
        model = self._usable_model()
        if model is None:
            return fallback
        try:
            classification, usage = classify_with_model(model, extraction)
        except ModelFailed:
            return fallback
        self._spend(usage)
        return classification

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


def _fields(extraction: Extraction | None) -> dict[str, Any]:
    return extraction.to_record() if extraction else {}
