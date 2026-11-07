import logging
import uuid

import pytest
from fastapi.testclient import TestClient


def access_lines(caplog: pytest.LogCaptureFixture) -> list[logging.LogRecord]:
    return [r for r in caplog.records if r.name == "jalada.http"]


def test_every_response_carries_a_request_id(client: TestClient) -> None:
    first = client.get("/health").headers["x-request-id"]
    second = client.get("/health").headers["x-request-id"]

    assert len(first) == 32 and first != second


def test_a_plain_incoming_request_id_is_kept_and_anything_else_replaced(
    client: TestClient,
) -> None:
    kept = client.get("/health", headers={"X-Request-ID": "web-abc-123456"})
    replaced = client.get("/health", headers={"X-Request-ID": "bad id\n"})

    assert kept.headers["x-request-id"] == "web-abc-123456"
    assert replaced.headers["x-request-id"] != "bad id\n"


def test_one_line_per_request_with_the_route_pattern_and_who_asked(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    body = {"email": "jane@example.com", "password": "correct horse battery", "display_name": "J"}
    user_id = client.post("/v1/auth/signup", json=body).json()["id"]
    entry_id = uuid.uuid4()

    caplog.clear()
    with caplog.at_level(logging.INFO, logger="jalada.http"):
        client.post(f"/v1/entries/{entry_id}/confirm?secret=1")

    [line] = access_lines(caplog)
    assert line.route == "/v1/entries/{entry_id}/confirm"  # type: ignore[attr-defined]
    assert line.method == "POST"  # type: ignore[attr-defined]
    assert line.status == 404  # type: ignore[attr-defined]
    assert line.user_id == user_id  # type: ignore[attr-defined]
    assert str(entry_id) not in line.getMessage()


def test_unknown_addresses_are_logged_as_unmatched(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.clear()
    with caplog.at_level(logging.INFO, logger="jalada.http"):
        client.get("/no/such/place")

    [line] = access_lines(caplog)
    assert line.route == "unmatched"  # type: ignore[attr-defined]
    assert line.status == 404  # type: ignore[attr-defined]
