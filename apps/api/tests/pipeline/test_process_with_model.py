from datetime import date
from decimal import Decimal

from fakes import ScriptedModel
from samples import CERTIFICATE, MPESA_SENT

from jalada.pipeline.model import ImageInput, ModelFailed
from jalada.pipeline.process import run_pipeline
from jalada.pipeline.run_types import Budget, EvidenceInput, PipelineResult

TODAY = date(2026, 11, 5)
PHOTO = ImageInput(b"jpeg", "image/jpeg")
RECEIPT = {
    "kind": "receipt",
    "occurred_on": "2026-11-04",
    "direction": "out",
    "amount_ksh": "250.00",
    "counterparty": "SAMPLE SHOP",
    "confidence": 0.9,
}
DEFAULT_BUDGET = Budget()
STOCK = {"purpose": "business", "category": "business_stock", "confidence": 0.9}


def run(
    evidence: EvidenceInput, model: ScriptedModel, budget: Budget = DEFAULT_BUDGET
) -> PipelineResult:
    return run_pipeline(evidence, {}, lambda _: False, TODAY, budget, model)


def test_a_photo_the_rules_cannot_read_goes_to_the_model() -> None:
    model = ScriptedModel(RECEIPT, STOCK)

    result = run(EvidenceInput(None, "image/jpeg", PHOTO), model)

    assert result.outcome == "proposed"
    assert result.extraction is not None and result.extraction.amount_cents == 25000
    assert result.classification is not None and result.classification.category == "business_stock"
    assert model.calls[0]["image"] == PHOTO
    assert result.usage.tokens == 300 and result.usage.cost_usd == Decimal("0.002")


def test_rules_come_first_and_the_model_only_classifies() -> None:
    model = ScriptedModel(STOCK)

    result = run(EvidenceInput(MPESA_SENT, "text/plain"), model)

    assert len(model.calls) == 1, "rules extracted the message; only classification used the model"
    assert result.extraction is not None and result.extraction.mpesa_code == "UK5AB1CD23"


def test_a_certificate_never_reaches_the_model() -> None:
    model = ScriptedModel()

    assert run(EvidenceInput(CERTIFICATE, "application/pdf"), model).outcome == "proposed"
    assert model.calls == []


def test_an_unsure_model_answer_goes_to_review() -> None:
    result = run(
        EvidenceInput(None, "image/jpeg", PHOTO),
        ScriptedModel({**RECEIPT, "confidence": 0.4}, STOCK),
    )

    assert result.outcome == "needs_review"
    assert result.verdict is not None
    assert result.verdict.review_reasons == ["amount or date not certain"]


def test_a_wrong_model_answer_is_retried_with_feedback() -> None:
    future = {**RECEIPT, "occurred_on": "2027-01-01"}
    model = ScriptedModel(future, STOCK, RECEIPT, STOCK)

    result = run(EvidenceInput(None, "image/jpeg", PHOTO), model)

    assert result.outcome == "proposed"
    assert result.attempts == 2
    assert "date is in the future" in model.calls[2]["content"]


def test_the_verifier_failing_twice_stops_the_run() -> None:
    future = {**RECEIPT, "occurred_on": "2027-01-01"}
    model = ScriptedModel(future, STOCK, future, STOCK, RECEIPT, STOCK)

    result = run(EvidenceInput(None, "image/jpeg", PHOTO), model)

    assert result.outcome == "needs_review"
    assert result.attempts == 2
    assert len(model.calls) == 4


def test_no_model_call_once_the_budget_is_spent() -> None:
    model = ScriptedModel(RECEIPT, STOCK, tokens=10_000)

    result = run(EvidenceInput(None, "image/jpeg", PHOTO), model, Budget(max_tokens=8000))

    assert len(model.calls) == 1, "the first call used the whole budget"
    assert result.classification is not None and result.classification.source == "none"
    assert result.outcome == "needs_review"


def test_a_failing_provider_sends_the_evidence_to_review() -> None:
    result = run(EvidenceInput(None, "image/jpeg", PHOTO), ScriptedModel(ModelFailed("timeout")))

    assert result.outcome == "needs_review"
    assert result.steps[-1].verdict == "model failed"


def test_model_steps_record_tokens_but_not_the_evidence() -> None:
    result = run(EvidenceInput(None, "image/jpeg", PHOTO), ScriptedModel(RECEIPT, STOCK))

    extract = next(step for step in result.steps if step.input.get("method") == "model")
    assert extract.input["model"] == "scripted"
    assert extract.input["input_tokens"] == 100
    assert "jpeg" not in repr(extract.input)
