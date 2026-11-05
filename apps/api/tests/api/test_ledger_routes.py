import uuid
from datetime import date

from fakes import Store
from fastapi.testclient import TestClient
from samples import confirmed_entry


def signed_in_user(client: TestClient, store: Store) -> uuid.UUID:
    body = {"email": "jane@example.com", "password": "correct horse battery", "display_name": "J"}
    return uuid.UUID(client.post("/v1/auth/signup", json=body).json()["id"])


def test_the_ledger_pages_with_a_cursor(client: TestClient, store: Store) -> None:
    user = signed_in_user(client, store)
    for day in range(1, 61):
        entry = confirmed_entry(
            user, date(2026, 3, 1).replace(day=1 + day % 28), 1_000, "out", "personal_food"
        )
        store.entries[entry.id] = entry

    first = client.get("/v1/entries").json()
    second = client.get("/v1/entries", params={"cursor": first["next_cursor"]}).json()

    assert len(first["items"]) == 50 and len(second["items"]) == 10
    assert second["next_cursor"] is None
    ids = [item["id"] for item in first["items"] + second["items"]]
    assert len(set(ids)) == 60


def test_ledger_filters_come_from_the_query(client: TestClient, store: Store) -> None:
    user = signed_in_user(client, store)
    for entry in [
        confirmed_entry(user, date(2026, 1, 5), 4_000_000, "in", "consultancy_fees"),
        confirmed_entry(user, date(2026, 2, 3), 80_000, "out", "personal_food"),
    ]:
        store.entries[entry.id] = entry

    february = client.get("/v1/entries", params={"from": "2026-02-01", "to": "2026-02-28"}).json()
    income = client.get("/v1/entries", params={"direction": "in"}).json()

    assert [i["category"] for i in february["items"]] == ["personal_food"]
    assert [i["category_name"] for i in income["items"]] == ["Consultancy or freelance fees"]


def test_the_monthly_summary_has_twelve_months_in_cents(client: TestClient, store: Store) -> None:
    user = signed_in_user(client, store)
    entry = confirmed_entry(user, date(2026, 1, 5), 4_000_000, "in", "consultancy_fees")
    store.entries[entry.id] = entry

    year = client.get("/v1/summary/monthly", params={"year": 2026}).json()

    assert year["year"] == 2026 and len(year["months"]) == 12
    assert year["months"][0] == {
        "month": 1,
        "in_business_cents": 4_000_000,
        "in_personal_cents": 0,
        "out_business_cents": 0,
        "out_personal_cents": 0,
    }


def test_a_made_up_cursor_starts_from_the_beginning(client: TestClient, store: Store) -> None:
    signed_in_user(client, store)

    assert client.get("/v1/entries", params={"cursor": "not-a-cursor"}).status_code == 200


def test_categories_are_listed(client: TestClient) -> None:
    categories = client.get("/v1/categories").json()

    assert {
        "slug": "salary",
        "name": "Salary",
        "direction": "in",
        "purpose": "personal",
    } in categories
    assert len(categories) == 23
