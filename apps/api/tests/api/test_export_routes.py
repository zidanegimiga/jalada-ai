import io
import uuid
from datetime import date

from fakes import Store
from fastapi.testclient import TestClient
from openpyxl import load_workbook
from samples import confirmed_entry


def sign_up(client: TestClient, email: str = "jane@example.com") -> uuid.UUID:
    body = {"email": email, "password": "correct horse battery", "display_name": "Jane"}
    return uuid.UUID(client.post("/v1/auth/signup", json=body).json()["id"])


def test_the_workbook_downloads_as_an_attachment(client: TestClient, store: Store) -> None:
    user = sign_up(client)
    entry = confirmed_entry(user, date(2026, 1, 31), 6_000_000, "in", "salary")
    store.entries[entry.id] = entry

    response = client.get("/v1/exports/2026.xlsx")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert response.headers["content-disposition"] == 'attachment; filename="jalada-2026.xlsx"'
    assert response.headers["cache-control"] == "private, no-store"
    income = load_workbook(io.BytesIO(response.content))["Income"]
    assert any(row[3].value == 60000 for row in income.iter_rows())


def test_the_workbook_only_holds_my_own_entries(client: TestClient, store: Store) -> None:
    sign_up(client)
    stranger = confirmed_entry(uuid.uuid4(), date(2026, 1, 31), 6_000_000, "in", "salary")
    store.entries[stranger.id] = stranger

    income = load_workbook(io.BytesIO(client.get("/v1/exports/2026.xlsx").content))["Income"]

    assert not any(row[3].value == 60000 for row in income.iter_rows())


def test_the_year_must_be_sensible(client: TestClient) -> None:
    sign_up(client)

    assert client.get("/v1/exports/1999.xlsx").status_code == 422
    assert client.get("/v1/exports/twenty.xlsx").status_code == 422


def test_the_export_needs_a_signed_in_user(client: TestClient) -> None:
    assert client.get("/v1/exports/2026.xlsx").status_code == 401
