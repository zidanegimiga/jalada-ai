from decimal import Decimal
from typing import Any

import pytest
from conftest import make_settings
from pydantic import SecretStr, ValidationError

from jalada.adapters.builders import build_budget, build_language_model
from jalada.adapters.models.gemini import GeminiModel
from jalada.adapters.models.ollama import OllamaModel
from jalada.config.settings import Settings


def settings(**changes: Any) -> Settings:
    """Test settings with some values changed, validated again like at startup."""
    return Settings.model_validate({**make_settings().model_dump(), **changes})


def test_no_model_by_default() -> None:
    assert build_language_model(make_settings()) is None


def test_gemini_is_built_with_its_default_model_and_prices() -> None:
    model = build_language_model(
        settings(model_provider="gemini", gemini_api_key=SecretStr("k"), model_input_price="0.30")
    )

    assert isinstance(model, GeminiModel)
    assert model.name == "gemini/gemini-2.5-flash"


def test_ollama_is_built_with_a_chosen_model() -> None:
    model = build_language_model(settings(model_provider="ollama", model_name="gemma3:4b"))

    assert isinstance(model, OllamaModel)
    assert model.name == "ollama/gemma3:4b"


def test_gemini_without_a_key_stops_startup() -> None:
    with pytest.raises(ValidationError, match="JALADA_GEMINI_API_KEY"):
        settings(model_provider="gemini")


@pytest.mark.parametrize("provider", ["gemini", "ollama"])
def test_production_refuses_a_model_not_cleared_for_real_data(provider: str) -> None:
    with pytest.raises(ValidationError, match="decision 0012"):
        settings(environment="production", model_provider=provider, gemini_api_key=SecretStr("k"))


def test_production_accepts_a_model_cleared_for_real_data() -> None:
    cleared = settings(
        environment="production",
        model_provider="gemini",
        gemini_api_key=SecretStr("k"),
        model_allowed_for_real_data=True,
    )

    assert cleared.model_provider == "gemini"


def test_the_budget_comes_from_settings() -> None:
    budget = build_budget(
        settings(pipeline_max_attempts=2, pipeline_max_tokens=500, pipeline_max_cost_usd="0.01")
    )

    assert (budget.max_attempts, budget.max_tokens, budget.max_cost_usd) == (
        2,
        500,
        Decimal("0.01"),
    )
