import json
import os

import pytest
from conftest import make_settings
from pydantic import SecretStr

from jalada.composition import build_services
from jalada.core.settings import Settings

pytestmark = pytest.mark.integration


def settings(**changes: object) -> Settings:
    return Settings.model_validate({**make_settings().model_dump(), **changes})


def test_the_assistant_is_not_built_unless_switched_on() -> None:
    assert build_services(make_settings()).conversations is None


def test_the_assistant_is_built_on_the_model_chain_when_switched_on() -> None:
    services = build_services(
        settings(
            database_url=os.environ["JALADA_TEST_DATABASE_URL"],
            agent_enabled=True,
            model_chain="ollama-qwen2.5vl",
            model_providers=SecretStr(json.dumps({"ollama": {"base_url": "http://localhost:1"}})),
        )
    )

    assert services.conversations is not None
