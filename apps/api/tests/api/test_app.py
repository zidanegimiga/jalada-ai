from collections.abc import Callable

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

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

    client = TestClient(build_api())

    assert client.get("/health").status_code == 200
