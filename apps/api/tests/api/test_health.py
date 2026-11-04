from fastapi.testclient import TestClient

from jalada.api.app import create_app
from jalada.config.settings import Settings


def test_health_reports_ok() -> None:
    client = TestClient(create_app(Settings(environment="test")))

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
