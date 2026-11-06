from fastapi.testclient import TestClient


def test_health_reports_ok_and_the_running_version(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "development"}
