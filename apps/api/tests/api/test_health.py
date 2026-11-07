from collections.abc import Callable

from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_health_reports_ok_and_the_running_version(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "development"}


class Check:
    def __init__(self, name: str, ok: bool) -> None:
        self.name = name
        self._ok = ok

    def ok(self) -> bool:
        return self._ok


def test_ready_when_every_check_passes(make_app: Callable[..., FastAPI]) -> None:
    app = make_app(health_checks=[Check("database", True), Check("storage", True)])

    response = TestClient(app).get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "version": "development",
        "checks": {"database": "ok", "storage": "ok"},
    }


def test_not_ready_names_the_failing_check_and_nothing_more(
    make_app: Callable[..., FastAPI],
) -> None:
    app = make_app(health_checks=[Check("database", True), Check("storage", False)])

    response = TestClient(app).get("/health/ready")

    assert response.status_code == 503
    assert response.json()["checks"] == {"database": "ok", "storage": "failing"}
