import json
from decimal import Decimal
from typing import Any

import pytest
from conftest import make_settings
from pydantic import SecretStr, ValidationError

from jalada.builders import build_budget, build_language_model
from jalada.core.settings import Settings
from jalada.modules.pipeline.adapters.models.chain import ModelChain
from jalada.modules.pipeline.adapters.models.gemini import GeminiModel
from jalada.modules.pipeline.adapters.models.openai_compatible import OpenAICompatibleModel
from jalada.modules.pipeline.adapters.models.registry import ModelSetupError

GEMINI = SecretStr(json.dumps({"gemini": {"api_key": "test-key"}}))


def settings(**changes: Any) -> Settings:
    """Test settings with some values changed, validated again like at startup."""
    return Settings.model_validate({**make_settings().model_dump(), **changes})


def test_no_model_by_default() -> None:
    assert build_language_model(make_settings()) is None


def test_the_chain_follows_the_order_given() -> None:
    model = build_language_model(
        settings(model_chain="gemini-3.5-flash-lite, gemini-3.1-flash-lite", model_providers=GEMINI)
    )

    assert isinstance(model, ModelChain)
    assert [link.profile.name for link in model.links] == [
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
    ]
    assert all(isinstance(link.model, GeminiModel) for link in model.links)
    assert model.links[0].profile.input_price == Decimal("0.30")


def test_a_model_outside_the_catalogue_stops_startup() -> None:
    with pytest.raises(ModelSetupError, match="gemini-9"):
        build_language_model(settings(model_chain="gemini-9", model_providers=GEMINI))


def test_a_model_without_its_provider_entry_stops_startup() -> None:
    with pytest.raises(ModelSetupError, match="JALADA_MODEL_PROVIDERS"):
        build_language_model(settings(model_chain="gemini-3.5-flash-lite"))


def test_gemini_without_a_key_stops_startup() -> None:
    no_key = SecretStr(json.dumps({"gemini": {}}))
    with pytest.raises(ModelSetupError, match="api_key"):
        build_language_model(settings(model_chain="gemini-3.5-flash-lite", model_providers=no_key))


def test_broken_provider_settings_never_echo_the_secret() -> None:
    broken = SecretStr('{"gemini": {"api_key": "AIza-very-secret"')

    with pytest.raises(ModelSetupError) as error:
        build_language_model(settings(model_chain="gemini-3.5-flash-lite", model_providers=broken))

    assert "AIza-very-secret" not in str(error.value)


def test_a_new_model_needs_only_settings() -> None:
    extra = json.dumps(
        [
            {
                "name": "router-model",
                "provider": "openai_compatible",
                "account": "openrouter",
                "model": "vendor/some-model",
                "vision": True,
                "input_price": "0.10",
            }
        ]
    )
    accounts = SecretStr(
        json.dumps({"openrouter": {"api_key": "k", "base_url": "https://router.example.com/v1"}})
    )

    model = build_language_model(
        settings(model_chain="router-model", extra_models=extra, model_providers=accounts)
    )

    assert isinstance(model, ModelChain)
    [link] = model.links
    assert isinstance(link.model, OpenAICompatibleModel)
    assert link.model.name == "openrouter/vendor/some-model"


def test_an_openai_compatible_account_needs_an_address() -> None:
    extra = json.dumps([{"name": "x", "provider": "openai_compatible", "model": "m"}])
    accounts = SecretStr(json.dumps({"openai_compatible": {"api_key": "k"}}))

    with pytest.raises(ModelSetupError, match="base_url"):
        build_language_model(
            settings(model_chain="x", extra_models=extra, model_providers=accounts)
        )


def test_production_refuses_models_not_cleared_for_real_data() -> None:
    with pytest.raises(ValidationError, match="decision 0012"):
        settings(environment="production", model_chain="gemini-3.5-flash-lite")


def test_production_accepts_models_cleared_for_real_data() -> None:
    cleared = settings(
        environment="production",
        model_chain="gemini-3.5-flash-lite",
        model_allowed_for_real_data=True,
    )

    assert cleared.model_chain_names == ["gemini-3.5-flash-lite"]


def test_the_budget_comes_from_settings() -> None:
    budget = build_budget(
        settings(pipeline_max_attempts=2, pipeline_max_tokens=500, pipeline_max_cost_usd="0.01")
    )

    assert (budget.max_attempts, budget.max_tokens, budget.max_cost_usd) == (
        2,
        500,
        Decimal("0.01"),
    )
