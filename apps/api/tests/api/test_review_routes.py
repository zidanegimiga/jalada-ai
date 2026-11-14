import pytest
from fastapi.testclient import TestClient
from samples import JPEG


def sign_up(client: TestClient, email: str = "jane@example.com") -> None:
    body = {"email": email, "password": "correct horse battery", "display_name": "Jane"}
    assert client.post("/v1/auth/signup", json=body).status_code == 201


@pytest.fixture
def waiting(client: TestClient) -> str:
    """A photo nothing could read, so it waits in the review queue with no entry."""
    sign_up(client)
    evidence_id = client.post("/v1/evidence", files={"file": ("r.jpg", JPEG)}).json()["id"]
    return str(evidence_id)


ENTRY = {
    "occurred_on": "2026-11-04",
    "amount": "1,250.00",
    "direction": "out",
    "counterparty": "SAMPLE SHOP",
    "category": "business_stock",
}


def test_typing_in_an_entry_reads_the_amount_as_shillings(client: TestClient, waiting: str) -> None:
    response = client.post(f"/v1/evidence/{waiting}/entry", json=ENTRY)

    assert response.status_code == 201
    entry = response.json()
    assert entry["amount_cents"] == 125000
    assert entry["status"] == "confirmed"
    assert entry["purpose"] == "business"
    assert entry["category_name"] == "Stock and supplies"


@pytest.mark.parametrize("amount", ["about 1000", 12.5, 1250, "-5.00", "0"])
def test_amounts_must_be_written_as_shillings(
    client: TestClient, waiting: str, amount: object
) -> None:
    response = client.post(f"/v1/evidence/{waiting}/entry", json={**ENTRY, "amount": amount})

    assert response.status_code == 422


def test_a_correction_that_does_not_fit_explains_why(client: TestClient, waiting: str) -> None:
    response = client.post(f"/v1/evidence/{waiting}/entry", json={**ENTRY, "category": "salary"})

    assert response.status_code == 422
    assert response.json()["error"] == {
        "code": "invalid_entry",
        "message": "That category does not fit money going this way.",
    }


def test_review_routes_need_my_own_entries(client: TestClient, waiting: str) -> None:
    entry_id = client.post(f"/v1/evidence/{waiting}/entry", json=ENTRY).json()["id"]
    client.cookies.clear()
    sign_up(client, "someone@example.com")

    assert client.post(f"/v1/entries/{entry_id}/confirm").status_code == 404
    assert (
        client.patch(f"/v1/entries/{entry_id}", json={"category": "personal_food"}).status_code
        == 404
    )
    assert client.post(f"/v1/evidence/{waiting}/entry", json=ENTRY).status_code == 404
    assert client.post(f"/v1/evidence/{waiting}/not-a-transaction").status_code == 404
    assert client.get("/v1/review").json()["items"] == []


def test_marking_not_a_transaction_takes_it_off_the_list(client: TestClient, waiting: str) -> None:
    response = client.post(f"/v1/evidence/{waiting}/not-a-transaction")

    assert response.status_code == 204
    assert client.get("/v1/review").json()["items"] == []
    assert client.get(f"/v1/evidence/{waiting}").json()["status"] == "not_a_transaction"


def test_review_needs_a_signed_in_user(client: TestClient) -> None:
    assert client.get("/v1/review").status_code == 401
