import json

import pytest
from conftest import make_settings
from pydantic import SecretStr
from sqlalchemy import Engine

from jalada.composition import build_job_runner, build_services
from jalada.core.settings import Settings
from jalada.modules.agent.application.channels import ANSWER_QUESTION_JOB

pytestmark = pytest.mark.integration


def settings(**changes: object) -> Settings:
    return Settings.model_validate({**make_settings().model_dump(), **changes})


def test_the_assistant_is_not_built_unless_switched_on() -> None:
    assert build_services(make_settings()).conversations is None


def test_the_assistant_is_built_on_the_model_chain_when_switched_on(engine: Engine) -> None:
    """Needs Postgres: the assistant sets up its checkpoint tables when it is built."""
    services = build_services(
        settings(
            database_url=engine.url.render_as_string(hide_password=False),
            agent_enabled=True,
            model_chain="ollama-qwen2.5vl",
            model_providers=SecretStr(json.dumps({"ollama": {"base_url": "http://localhost:1"}})),
        )
    )

    assert services.conversations is not None


def test_with_the_bot_on_telegram_questions_are_routed_and_answered(engine: Engine) -> None:
    on = settings(
        database_url=engine.url.render_as_string(hide_password=False),
        agent_enabled=True,
        model_chain="ollama-qwen2.5vl",
        model_providers=SecretStr(json.dumps({"ollama": {"base_url": "http://localhost:1"}})),
        telegram_bot_token=SecretStr("123:test"),
        telegram_bot_username="jalada_test_bot",
    )

    capture = build_services(on).telegram_capture
    runner = build_job_runner(on)

    assert capture is not None and capture._assistant is not None
    assert ANSWER_QUESTION_JOB in runner._handlers


def test_with_the_assistant_off_telegram_keeps_every_text_as_evidence(engine: Engine) -> None:
    off = settings(
        database_url=engine.url.render_as_string(hide_password=False),
        telegram_bot_token=SecretStr("123:test"),
        telegram_bot_username="jalada_test_bot",
    )

    capture = build_services(off).telegram_capture

    assert capture is not None and capture._assistant is None
    assert ANSWER_QUESTION_JOB not in build_job_runner(off)._handlers
