import pytest
from fastapi.testclient import TestClient

from jalada.api.app import create_app
from jalada.composition import build_api
from jalada.config.settings import Settings


def test_api_docs_are_served_outside_production() -> None:
    client = TestClient(create_app(Settings(environment="development")))

    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200


def test_api_docs_are_hidden_in_production() -> None:
    client = TestClient(create_app(Settings(environment="production")))

    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_composition_root_builds_the_api_from_the_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("JALADA_ENVIRONMENT", "test")

    client = TestClient(build_api())

    assert client.get("/health").status_code == 200
