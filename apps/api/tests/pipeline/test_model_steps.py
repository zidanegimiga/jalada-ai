from datetime import date
from typing import Any

import pytest
from fakes import ScriptedModel

from jalada.modules.evidence.domain.evidence import EvidenceKind
from jalada.modules.ledger.domain.categories import Direction, Purpose
from jalada.modules.pipeline.domain.extraction import Extraction
from jalada.modules.pipeline.domain.model import ImageInput
from jalada.modules.pipeline.domain.model_steps import classify_with_model, extract_with_model

PHOTO = ImageInput(b"jpeg", "image/jpeg")
GOOD = {
    "kind": "receipt",
    "occurred_on": "2026-11-04",
    "direction": "out",
    "amount_ksh": "1,250.00",
    "counterparty": "  SAMPLE   SHOP ",
    "confidence": 0.92,
}
PAYMENT = Extraction(EvidenceKind.RECEIPT, date(2026, 11, 4), Direction.OUT, 125000, "SAMPLE SHOP")


def test_a_good_reply_becomes_an_extraction_in_cents() -> None:
    extraction, confidence, reply = extract_with_model(ScriptedModel(GOOD), "text", None, [])

    assert extraction is not None
    assert extraction.amount_cents == 125000
    assert extraction.occurred_on == date(2026, 11, 4)
    assert extraction.direction == Direction.OUT
    assert extraction.counterparty == "SAMPLE SHOP"
    assert extraction.kind == EvidenceKind.RECEIPT
    assert confidence == 0.92
    assert reply.usage.tokens == 150


@pytest.mark.parametrize(
    ("change", "check"),
    [
        ({"amount_ksh": "about a thousand"}, lambda e, c: e is None),
        ({"amount_ksh": 1250.5}, lambda e, c: e is None),  # numbers are refused: money is text
        ({"occurred_on": "04/11/2026"}, lambda e, c: e.occurred_on is None),
        ({"direction": "sideways"}, lambda e, c: e.direction is None),
        ({"kind": "invoice"}, lambda e, c: e.kind == EvidenceKind.UNKNOWN),
        ({"confidence": 7}, lambda e, c: c == 1.0),
        ({"confidence": "high"}, lambda e, c: c == 0.0),
        ({"counterparty": "x" * 500}, lambda e, c: len(e.counterparty) == 200),
    ],
)
def test_untrusted_fields_are_checked(change: dict[str, Any], check: Any) -> None:
    extraction, confidence, _ = extract_with_model(
        ScriptedModel({**GOOD, **change}), "text", None, []
    )

    assert check(extraction, confidence)


def test_the_photo_is_sent_only_when_there_is_no_text() -> None:
    with_text, without_text = ScriptedModel(GOOD), ScriptedModel(GOOD)

    extract_with_model(with_text, "SAMPLE SHOP 1,250.00", PHOTO, [])
    extract_with_model(without_text, None, PHOTO, [])

    assert with_text.calls[0]["image"] is None
    assert without_text.calls[0]["image"] == PHOTO


def test_verifier_problems_are_passed_back_as_feedback() -> None:
    model = ScriptedModel(GOOD)

    extract_with_model(model, "text", None, ["date is in the future"])

    assert "date is in the future" in model.calls[0]["content"]


def test_long_text_is_cut_to_stay_in_budget() -> None:
    model = ScriptedModel(GOOD)

    extract_with_model(model, "x" * 50_000, None, [])

    assert len(model.calls[0]["content"]) < 6100


def test_a_cost_category_sets_the_purpose() -> None:
    reply = {"purpose": "personal", "category": "business_stock", "confidence": 0.9}

    classification, _ = classify_with_model(ScriptedModel(reply), PAYMENT)

    assert (classification.category, classification.purpose) == ("business_stock", Purpose.BUSINESS)
    assert classification.source == "model"


@pytest.mark.parametrize("category", ["salary", "made_up_category", None])
def test_categories_that_do_not_fit_become_unsure(category: str | None) -> None:
    reply = {"purpose": "business", "category": category, "confidence": 0.99}

    classification, _ = classify_with_model(ScriptedModel(reply), PAYMENT)

    assert classification.category is None
    assert classification.purpose == Purpose.UNSURE
    assert classification.confidence == 0.0


def test_the_model_is_only_offered_categories_for_the_direction() -> None:
    model = ScriptedModel({"purpose": "unsure", "category": None, "confidence": 0})

    classify_with_model(model, PAYMENT)

    offered = model.calls[0]["schema"]["properties"]["category"]["enum"]
    assert "business_stock" in offered and "salary" not in offered
