from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from jalada.api.app import create_app
from jalada.composition import build_api


def test_api_docs_are_served_outside_production(make_app: Callable[..., FastAPI]) -> None:
    client = TestClient(make_app("development"))

    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200


def test_api_docs_are_hidden_in_production(make_app: Callable[..., FastAPI]) -> None:
    client = TestClient(make_app("production"))

    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_composition_root_builds_the_api_from_the_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("JALADA_ENVIRONMENT", "test")
    monkeypatch.setenv("JALADA_DATABASE_URL", "postgresql+psycopg://u:p@localhost:1/unused")
    monkeypatch.setenv("JALADA_STORAGE_ACCESS_KEY", "access")
    monkeypatch.setenv("JALADA_STORAGE_SECRET_KEY", "secret")
    monkeypatch.setenv("JALADA_EVIDENCE_KEYS", "dGVzdC1rZXktZm9yLWV2aWRlbmNlLTMyLWJ5dGVzISE=")

    client = TestClient(build_api())

    assert client.get("/health").status_code == 200


def test_the_api_can_run_the_job_loop_while_it_is_up(make_app: Callable[..., FastAPI]) -> None:
    events: list[str] = []

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        events.append("started")
        yield
        events.append("stopped")

    base = make_app()
    app = create_app(base.state.settings, base.state.services, lifespan)

    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        assert events == ["started"]

    assert events == ["started", "stopped"]
