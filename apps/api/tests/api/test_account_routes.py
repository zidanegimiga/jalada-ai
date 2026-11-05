import io
import zipfile

from fastapi.testclient import TestClient
from samples import JPEG


def sign_up(client: TestClient, email: str = "jane@example.com") -> None:
    body = {"email": email, "password": "correct horse battery", "display_name": "Jane"}
    assert client.post("/v1/auth/signup", json=body).status_code == 201


def test_the_export_downloads_as_a_zip(client: TestClient) -> None:
    sign_up(client)
    client.post("/v1/evidence", files={"file": ("r.jpg", JPEG)})

    response = client.get("/v1/account/export")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert response.headers["content-disposition"] == 'attachment; filename="jalada-data.zip"'
    assert response.headers["cache-control"] == "private, no-store"
    archive = zipfile.ZipFile(io.BytesIO(response.content))
    assert any(name.endswith(".jpg") for name in archive.namelist())


def test_the_export_needs_a_signed_in_user(client: TestClient) -> None:
    assert client.get("/v1/account/export").status_code == 401


def test_deleting_the_account_signs_out_and_cannot_be_undone(client: TestClient) -> None:
    sign_up(client)

    response = client.request("DELETE", "/v1/account", json={"email": "jane@example.com"})

    assert response.status_code == 204
    assert 'jalada_session=""' in response.headers["set-cookie"]
    assert client.get("/v1/me").status_code == 401
    signed_in = client.post(
        "/v1/auth/login", json={"email": "jane@example.com", "password": "correct horse battery"}
    )
    assert signed_in.status_code == 401


def test_deleting_needs_the_email_typed_exactly(client: TestClient) -> None:
    sign_up(client)

    response = client.request("DELETE", "/v1/account", json={"email": "someone@example.com"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "confirmation_mismatch"
    assert client.get("/v1/me").status_code == 200


def test_deleting_needs_a_signed_in_user(client: TestClient) -> None:
    assert (
        client.request("DELETE", "/v1/account", json={"email": "x@example.com"}).status_code == 401
    )
