import uuid
from datetime import date

from fakes import Store
from fastapi.testclient import TestClient
from samples import certificate, deposit


def signed_in_user(client: TestClient) -> uuid.UUID:
    body = {"email": "jane@example.com", "password": "correct horse battery", "display_name": "J"}
    return uuid.UUID(client.post("/v1/auth/signup", json=body).json()["id"])


def test_a_certificate_shows_its_suggestions_and_payments(client: TestClient, store: Store) -> None:
    user = signed_in_user(client)
    cert = certificate(user, date(2026, 3, 3), 4_000_000, 200_000, "CLIENT")
    paid = deposit(user, date(2026, 3, 5), 3_800_000, "CLIENT")
    store.entries.update({cert.id: cert, paid.id: paid})

    shown = client.get(f"/v1/certificates/{cert.id}").json()
    linked = client.post(
        f"/v1/certificates/{cert.id}/payments", json={"payment_id": str(paid.id)}
    ).json()
    unlinked = client.delete(f"/v1/certificates/{cert.id}/payments/{paid.id}").json()

    assert shown["expected_payment_cents"] == 3_800_000
    assert [s["id"] for s in shown["suggestions"]] == [str(paid.id)]
    assert [p["id"] for p in linked["payments"]] == [str(paid.id)]
    assert linked["linked_cents"] == 3_800_000
    assert unlinked["payments"] == []


def test_a_bad_link_explains_itself(client: TestClient, store: Store) -> None:
    user = signed_in_user(client)
    cert = certificate(user, date(2026, 3, 3), 4_000_000, 200_000, "CLIENT")
    too_big = deposit(user, date(2026, 3, 5), 5_000_000, "CLIENT")
    store.entries.update({cert.id: cert, too_big.id: too_big})

    response = client.post(
        f"/v1/certificates/{cert.id}/payments", json={"payment_id": str(too_big.id)}
    )

    assert response.status_code == 422
    assert "gross amount" in response.json()["error"]["message"]


def test_another_users_certificate_is_not_found(client: TestClient, store: Store) -> None:
    signed_in_user(client)
    theirs = certificate(uuid.uuid4(), date(2026, 3, 3), 4_000_000, 200_000, "CLIENT")
    store.entries[theirs.id] = theirs

    assert client.get(f"/v1/certificates/{theirs.id}").status_code == 404


def test_certificates_need_a_signed_in_user(client: TestClient) -> None:
    assert client.get(f"/v1/certificates/{uuid.uuid4()}").status_code == 401


def test_the_ledger_marks_linked_certificates_and_payments(
    client: TestClient, store: Store
) -> None:
    user = signed_in_user(client)
    cert = certificate(user, date(2026, 3, 3), 4_000_000, 200_000, "CLIENT")
    paid = deposit(user, date(2026, 3, 5), 3_800_000, "CLIENT")
    store.entries.update({cert.id: cert, paid.id: paid})
    client.post(f"/v1/certificates/{cert.id}/payments", json={"payment_id": str(paid.id)})

    items = {item["id"]: item for item in client.get("/v1/entries").json()["items"]}

    assert items[str(cert.id)]["linked_payment_ids"] == [str(paid.id)]
    assert items[str(paid.id)]["linked_certificate_id"] == str(cert.id)
