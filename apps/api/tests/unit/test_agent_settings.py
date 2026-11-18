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
