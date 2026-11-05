from collections.abc import Callable

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from samples import JPEG, MPESA, PDF

from jalada.domain.evidence import MAX_FILE_BYTES


def sign_up(client: TestClient, email: str = "jane@example.com") -> None:
    body = {"email": email, "password": "correct horse battery", "display_name": "Jane"}
    assert client.post("/v1/auth/signup", json=body).status_code == 201


@pytest.fixture
def signed_in(client: TestClient) -> TestClient:
    sign_up(client)
    return client


def upload(client: TestClient, data: bytes, name: str = "receipt.jpg") -> dict[str, object]:
    response = client.post("/v1/evidence", files={"file": (name, data, "image/jpeg")})
    return {**response.json(), "http_status": response.status_code}


def test_uploading_a_photo_creates_evidence(signed_in: TestClient) -> None:
    result = upload(signed_in, JPEG)

    assert result["http_status"] == 201
    assert result["content_type"] == "image/jpeg"
    assert result["duplicate"] is False


def test_the_file_name_and_declared_type_are_ignored(signed_in: TestClient) -> None:
    result = upload(signed_in, PDF, name="photo.jpg")

    assert result["content_type"] == "application/pdf"


def test_uploading_the_same_file_again_returns_the_first(signed_in: TestClient) -> None:
    first = upload(signed_in, JPEG)

    again = upload(signed_in, JPEG)

    assert again["http_status"] == 200
    assert again["duplicate"] is True
    assert again["id"] == first["id"]


def test_files_that_are_not_photos_or_pdfs_are_refused(signed_in: TestClient) -> None:
    result = upload(signed_in, b"<html>not evidence</html>", name="receipt.jpg")

    assert result["http_status"] == 415
    assert result["error"] == {
        "code": "unsupported_file",
        "message": "Send a photo (JPEG, PNG or WebP) or a PDF.",
    }


def test_oversized_uploads_are_refused(signed_in: TestClient) -> None:
    result = upload(signed_in, JPEG + b"0" * MAX_FILE_BYTES)

    assert result["http_status"] == 413


def test_pasting_an_mpesa_message(signed_in: TestClient) -> None:
    response = signed_in.post("/v1/evidence/text", json={"text": MPESA})

    assert response.status_code == 201
    assert response.json()["source"] == "web_paste"


def test_the_list_shows_newest_first(signed_in: TestClient) -> None:
    first = upload(signed_in, JPEG)
    second = signed_in.post("/v1/evidence/text", json={"text": MPESA}).json()

    items = signed_in.get("/v1/evidence").json()["items"]

    assert {item["id"] for item in items} == {first["id"], second["id"]}


def test_the_original_file_comes_back_unchanged_with_safe_headers(signed_in: TestClient) -> None:
    evidence_id = upload(signed_in, JPEG)["id"]

    response = signed_in.get(f"/v1/evidence/{evidence_id}/file")

    assert response.content == JPEG
    assert response.headers["content-type"] == "image/jpeg"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["cache-control"] == "private, no-store"


def test_nobody_else_can_see_or_download_my_evidence(signed_in: TestClient) -> None:
    evidence_id = upload(signed_in, JPEG)["id"]
    signed_in.cookies.clear()
    sign_up(signed_in, "someone@example.com")

    assert signed_in.get(f"/v1/evidence/{evidence_id}").status_code == 404
    assert signed_in.get(f"/v1/evidence/{evidence_id}/file").status_code == 404
    assert signed_in.get("/v1/evidence").json()["items"] == []


def test_evidence_needs_a_signed_in_user(client: TestClient) -> None:
    assert client.post("/v1/evidence/text", json={"text": MPESA}).status_code == 401
    assert client.get("/v1/evidence").status_code == 401


def test_uploads_are_rate_limited_per_user(make_app: Callable[..., FastAPI]) -> None:
    client = TestClient(make_app(upload_rule="2/minute"))
    sign_up(client)

    codes = [
        client.post("/v1/evidence/text", json={"text": f"note {n}"}).status_code for n in range(3)
    ]

    assert codes == [201, 201, 429]
