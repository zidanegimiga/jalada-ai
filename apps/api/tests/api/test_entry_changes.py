from typing import Any

import pytest
from fakes import Store
from fastapi.testclient import TestClient
from transfers import TO_BANK, Paste

from jalada.modules.ledger.application import entry_changes

ENTRY = {
    "occurred_on": "2026-11-04",
    "amount": "1,250.00",
    "direction": "out",
    "counterparty": "SAMPLE SHOP",
    "category": "business_stock",
}


def sign_up(client: TestClient, email: str = "jane@example.com") -> None:
    body = {"email": email, "password": "correct horse battery", "display_name": "J"}
    assert client.post("/v1/auth/signup", json=body).status_code == 201


def typed_in(client: TestClient, counterparty: str) -> str:
    """A payment typed in by hand, on its own piece of evidence."""
    evidence = client.post("/v1/evidence/text", json={"text": f"Paid {counterparty}"}).json()
    entry = client.post(
        f"/v1/evidence/{evidence['id']}/entry", json={**ENTRY, "counterparty": counterparty}
    ).json()
    return str(entry["id"])


def changes(client: TestClient, after: str | None = None) -> dict[str, Any]:
    response = client.get("/v1/sync/entries", params={"after": after} if after else {})
    assert response.status_code == 200
    body: dict[str, Any] = response.json()
    return body


def names(page: dict[str, Any]) -> list[str]:
    return [c["entry"]["counterparty"] for c in page["changes"]]


def test_the_first_read_has_everything_and_the_next_only_what_changed(
    client: TestClient,
) -> None:
    sign_up(client)
    first = typed_in(client, "FIRST SHOP")
    typed_in(client, "SECOND SHOP")

    everything = changes(client)
    assert names(everything) == ["FIRST SHOP", "SECOND SHOP"]
    assert everything["more"] is False

    client.patch(f"/v1/entries/{first}", json={"counterparty": "RENAMED SHOP"})
    since = changes(client, str(everything["next"]))

    assert names(since) == ["RENAMED SHOP"]
    assert since["changes"][0]["version"] == 2
    assert changes(client, str(since["next"]))["changes"] == []


def test_a_long_feed_comes_in_pages(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(entry_changes, "PAGE_SIZE", 2)
    monkeypatch.setattr(entry_changes.EntryChanges.since, "__defaults__", (2,))
    sign_up(client)
    for n in range(3):
        typed_in(client, f"SHOP {n}")

    first = changes(client)
    rest = changes(client, str(first["next"]))

    assert (names(first), first["more"]) == (["SHOP 0", "SHOP 1"], True)
    assert (names(rest), rest["more"]) == (["SHOP 2"], False)


def test_entries_in_every_state_are_in_the_feed(
    client: TestClient, store: Store, paste: Paste
) -> None:
    sign_up(client)
    [user_id] = store.users
    payment_id = paste(TO_BANK, user=user_id)
    start = changes(client)
    [waiting] = start["changes"]
    assert waiting["entry"]["status"] != "confirmed"

    evidence_id = waiting["entry"]["evidence_id"]
    client.post(f"/v1/evidence/{evidence_id}/not-a-transaction")

    [change] = changes(client, str(start["next"]))["changes"]
    assert (change["id"], change["entry"]["status"]) == (str(payment_id), "rejected")


def test_nobody_sees_anyone_else_s_changes(client: TestClient) -> None:
    sign_up(client)
    typed_in(client, "JANE'S SHOP")
    client.cookies.clear()
    sign_up(client, "other@example.com")

    assert changes(client)["changes"] == []


def test_a_made_up_position_is_refused(client: TestClient) -> None:
    sign_up(client)

    assert client.get("/v1/sync/entries", params={"after": "not-a-cursor"}).status_code == 422
