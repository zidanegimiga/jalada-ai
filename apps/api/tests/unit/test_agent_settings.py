from decimal import Decimal
from typing import Any

import pytest
from conftest import make_settings
from pydantic import ValidationError

from jalada.builders import build_agent_budget
from jalada.core.settings import Settings


def settings(**changes: Any) -> Settings:
    return Settings.model_validate({**make_settings().model_dump(), **changes})


def test_the_assistant_is_off_by_default() -> None:
    assert make_settings().agent_enabled is False


def test_the_assistant_can_run_on_any_model_outside_production() -> None:
    assert settings(environment="development", agent_enabled=True, model_chain="m").agent_enabled


def test_the_assistant_needs_a_model() -> None:
    with pytest.raises(ValidationError, match="JALADA_MODEL_CHAIN"):
        settings(agent_enabled=True)


def test_production_refuses_the_assistant_on_models_not_cleared_for_real_data() -> None:
    with pytest.raises(ValidationError, match="decision 0012"):
        settings(environment="production", agent_enabled=True, model_chain="m")


def test_production_runs_the_assistant_on_models_cleared_for_real_data() -> None:
    cleared = settings(
        environment="production",
        agent_enabled=True,
        model_chain="m",
        model_allowed_for_real_data=True,
    )

    assert cleared.agent_enabled


def test_the_assistant_has_a_budget_per_question() -> None:
    budget = build_agent_budget(settings(agent_max_steps=3, agent_max_cost_usd="0.005"))

    assert (budget.max_steps, budget.max_cost_usd) == (3, Decimal("0.005"))


def test_the_fast_chain_falls_back_to_the_model_chain_and_deep_to_fast() -> None:
    plain = settings(model_chain="a, b")
    split = settings(model_chain="a", agent_chain_fast="f", agent_chain_deep="d1, d2")

    assert (plain.agent_fast_names, plain.agent_deep_names) == (["a", "b"], ["a", "b"])
    assert (split.agent_fast_names, split.agent_deep_names) == (["f"], ["d1", "d2"])


def test_production_holds_the_assistants_own_chains_to_the_real_data_rule() -> None:
    with pytest.raises(ValidationError, match="decision 0012"):
        settings(environment="production", agent_chain_deep="gemini-3.6-flash")
