import pytest
from fakes import FixedClock, Store
from fastapi.testclient import TestClient
from receipts import Send
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


@pytest.fixture
def asked(client: TestClient, store: Store, send: Send) -> str:
    """A receipt and its payment message for a signed-in user: one open question."""
    sign_up(client)
    [user_id] = store.users
    send("receipt", user=user_id)
    send("message", user=user_id)
    [suggestion] = store.suggestions.values()
    return str(suggestion.id)


def test_to_check_asks_if_a_receipt_belongs_to_the_payment(client: TestClient, asked: str) -> None:
    [item] = client.get("/v1/review").json()["items"]

    assert item["entry"]["amount_cents"] == 41900
    match = item["match"]
    assert match["suggestion_id"] == asked
    assert (match["counterparty"], match["amount_cents"]) == ("SAMPLE MUSIC SHOP", 41900)
    assert match["reasons"] == ["same amount", "same day"]
    assert match["receipt"]["content_type"] == "image/jpeg"


def test_yes_returns_the_payment_with_its_receipt(client: TestClient, asked: str) -> None:
    response = client.post(f"/v1/suggestions/{asked}/accept")

    assert response.status_code == 200
    assert response.json()["amount_cents"] == 41900
    [item] = client.get("/v1/review").json()["items"]
    assert item["match"] is None


def test_no_is_answered_once(client: TestClient, asked: str) -> None:
    assert client.post(f"/v1/suggestions/{asked}/decline").status_code == 204
    again = client.post(f"/v1/suggestions/{asked}/accept")

    assert again.status_code == 404
    assert again.json()["error"]["code"] == "not_found"


def test_a_question_belongs_to_its_user(client: TestClient, asked: str) -> None:
    client.cookies.clear()
    sign_up(client, "other@example.com")

    assert client.post(f"/v1/suggestions/{asked}/accept").status_code == 404
    assert client.post(f"/v1/suggestions/{asked}/decline").status_code == 404


def test_saying_how_a_receipt_was_paid(
    client: TestClient, store: Store, send: Send, clock: FixedClock
) -> None:
    sign_up(client)
    [user_id] = store.users
    send("receipt", user=user_id)
    [candidate] = store.transactions.values()

    response = client.post(f"/v1/receipts/{candidate.id}/paid", json={"paid_with": "cash"})

    assert response.status_code == 200
    assert response.json()["status"] == "needs_review"
    wrong = client.post(f"/v1/receipts/{candidate.id}/paid", json={"paid_with": "bitcoin"})
    assert wrong.status_code == 422


def test_not_a_transaction_can_be_taken_back(client: TestClient, waiting: str) -> None:
    client.post(f"/v1/evidence/{waiting}/not-a-transaction")

    assert client.delete(f"/v1/evidence/{waiting}/not-a-transaction").status_code == 204
    [item] = client.get("/v1/review").json()["items"]
    assert item["evidence"]["id"] == waiting
    again = client.delete(f"/v1/evidence/{waiting}/not-a-transaction")
    assert again.status_code == 422


def test_a_yes_can_be_taken_back(client: TestClient, asked: str) -> None:
    client.post(f"/v1/suggestions/{asked}/accept")

    response = client.post(f"/v1/suggestions/{asked}/undo")

    assert response.status_code == 200
    assert response.json()["amount_cents"] == 41900
    assert client.post(f"/v1/suggestions/{asked}/undo").status_code == 404
