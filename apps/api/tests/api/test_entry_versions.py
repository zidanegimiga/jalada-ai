import pytest
from fastapi.testclient import TestClient
from samples import JPEG

ENTRY = {
    "occurred_on": "2026-11-04",
    "amount": "1,250.00",
    "direction": "out",
    "counterparty": "SAMPLE SHOP",
    "category": "business_stock",
}


@pytest.fixture
def entry(client: TestClient) -> dict[str, object]:
    """A payment typed in by hand, so it is confirmed straight away."""
    body = {"email": "jane@example.com", "password": "correct horse battery", "display_name": "J"}
    assert client.post("/v1/auth/signup", json=body).status_code == 201
    evidence_id = client.post("/v1/evidence", files={"file": ("r.jpg", JPEG)}).json()["id"]
    created: dict[str, object] = client.post(f"/v1/evidence/{evidence_id}/entry", json=ENTRY).json()
    return created


def test_every_save_moves_the_version_on(client: TestClient, entry: dict[str, object]) -> None:
    first = entry["version"]
    assert isinstance(first, int)

    edited = client.patch(
        f"/v1/entries/{entry['id']}", json={"counterparty": "OTHER SHOP", "version": first}
    )

    assert edited.status_code == 200
    assert edited.json()["version"] == first + 1
    listed = client.get("/v1/entries").json()["items"][0]
    assert listed["version"] == first + 1


def test_an_edit_from_an_older_copy_changes_nothing_and_shows_the_current_one(
    client: TestClient, entry: dict[str, object]
) -> None:
    seen = entry["version"]
    client.patch(f"/v1/entries/{entry['id']}", json={"counterparty": "ON THE WEB", "version": seen})

    late = client.patch(
        f"/v1/entries/{entry['id']}", json={"counterparty": "QUEUED OFFLINE", "version": seen}
    )

    assert late.status_code == 409
    body = late.json()
    assert body["error"]["code"] == "changed_elsewhere"
    assert body["current"]["counterparty"] == "ON THE WEB"
    assert body["current"]["version"] == entry["version"] + 1  # type: ignore[operator]
    assert client.get(f"/v1/entries/{entry['id']}").json()["entry"]["counterparty"] == "ON THE WEB"


def test_confirming_from_an_older_copy_is_caught_too(
    client: TestClient, entry: dict[str, object]
) -> None:
    client.patch(f"/v1/entries/{entry['id']}", json={"counterparty": "ON THE WEB"})

    late = client.post(f"/v1/entries/{entry['id']}/confirm", json={"version": entry["version"]})

    assert late.status_code == 409


def test_edits_that_do_not_say_a_version_work_as_before(
    client: TestClient, entry: dict[str, object]
) -> None:
    assert client.post(f"/v1/entries/{entry['id']}/confirm").status_code == 200
    assert client.patch(f"/v1/entries/{entry['id']}", json={"counterparty": "X"}).status_code == 200


def test_a_version_must_be_a_positive_number(client: TestClient, entry: dict[str, object]) -> None:
    response = client.patch(f"/v1/entries/{entry['id']}", json={"version": 0})

    assert response.status_code == 422
