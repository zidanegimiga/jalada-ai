"""Turning model replies into extractions and classifications. Replies are never trusted as is."""

import json
from datetime import date
from typing import Any

from jalada.modules.evidence.domain.evidence import EvidenceKind
from jalada.modules.ledger.domain.categories import CATEGORIES, Direction, Purpose
from jalada.modules.pipeline.domain.extraction import Classification, Extraction
from jalada.modules.pipeline.domain.model import ImageInput, LanguageModel, ModelUsage
from jalada.modules.pipeline.domain.prompts import (
    CLASSIFICATION_INSTRUCTIONS,
    EXTRACTION_INSTRUCTIONS,
    EXTRACTION_SCHEMA,
    category_list,
    classification_schema,
)
from jalada.shared.money import to_cents

# Long documents are cut so one request stays inside the token budget.
MAX_TEXT_SENT = 6000


def extract_with_model(
    model: LanguageModel,
    text: str | None,
    image: ImageInput | None,
    feedback: list[str],
) -> tuple[Extraction | None, float, ModelUsage]:
    content = f"Evidence text:\n{text[:MAX_TEXT_SENT]}" if text else "The evidence is the photo."
    if feedback:
        content += "\n\nA check found these problems with your last answer: " + "; ".join(feedback)
    reply = model.complete(
        EXTRACTION_INSTRUCTIONS, content, EXTRACTION_SCHEMA, None if text else image
    )
    return _to_extraction(reply.data), _confidence(reply.data), reply.usage


def classify_with_model(
    model: LanguageModel, extraction: Extraction
) -> tuple[Classification, ModelUsage]:
    direction = extraction.direction or Direction.OUT
    details = {
        "direction": direction,
        "amount_ksh": f"{(extraction.amount_cents or 0) / 100:.2f}",
        "counterparty": extraction.counterparty,
        "reference": extraction.reference,
        "kind": extraction.kind,
    }
    content = (
        f"Categories:\n{category_list(direction)}\n\nPayment:\n{json.dumps(details, default=str)}"
    )
    reply = model.complete(CLASSIFICATION_INSTRUCTIONS, content, classification_schema(direction))
    return _to_classification(reply.data, direction), reply.usage


def _to_extraction(data: dict[str, Any]) -> Extraction | None:
    amount = _cents(data.get("amount_ksh"))
    if amount is None:
        return None
    return Extraction(
        kind=_choice(EvidenceKind, data.get("kind"), EvidenceKind.UNKNOWN),
        occurred_on=_date(data.get("occurred_on")),
        direction=_choice(Direction, data.get("direction"), None),
        amount_cents=amount,
        counterparty=_text(data.get("counterparty")),
        reference=_text(data.get("reference")),
        mpesa_code=_text(data.get("mpesa_code")),
        fee_cents=_cents(data.get("fee_ksh")),
        tax_withheld_cents=_cents(data.get("tax_withheld_ksh")),
    )


def _to_classification(data: dict[str, Any], direction: Direction) -> Classification:
    category = CATEGORIES.get(str(data.get("category")))
    if category is None or category.direction != direction:
        return Classification(Purpose.UNSURE, None, 0.0, "model")
    # The category already says business or personal; that wins over the model's purpose.
    return Classification(category.purpose, category.slug, _confidence(data), "model")


def _cents(value: Any) -> int | None:
    return to_cents(value) if isinstance(value, str) else None


def _date(value: Any) -> date | None:
    try:
        return date.fromisoformat(value) if isinstance(value, str) else None
    except ValueError:
        return None


def _text(value: Any) -> str | None:
    return " ".join(value.split())[:200] or None if isinstance(value, str) else None


def _choice[T](kind: type[T], value: Any, default: T) -> T:
    try:
        return kind(value)  # type: ignore[call-arg]
    except ValueError:
        return default


def _confidence(data: dict[str, Any]) -> float:
    value = data.get("confidence")
    return min(max(float(value), 0.0), 1.0) if isinstance(value, int | float) else 0.0
