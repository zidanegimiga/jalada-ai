from collections.abc import Callable

from fastapi import FastAPI
from fastapi.testclient import TestClient

SIGN_UP = {"email": "jane@example.com", "password": "correct horse battery", "display_name": "Jane"}
SIGN_IN = {"email": "jane@example.com", "password": "correct horse battery"}


def test_sign_up_returns_the_user_and_sets_an_http_only_cookie(client: TestClient) -> None:
    response = client.post("/v1/auth/signup", json=SIGN_UP)

    assert response.status_code == 201
    assert response.json()["email"] == "jane@example.com"
    cookie = response.headers["set-cookie"]
    assert cookie.startswith("jalada_session=")
    assert "HttpOnly" in cookie
    assert "SameSite=lax" in cookie


def test_the_session_cookie_identifies_the_user(client: TestClient) -> None:
    client.post("/v1/auth/signup", json=SIGN_UP)

    response = client.get("/v1/me")

    assert response.status_code == 200
    assert response.json()["display_name"] == "Jane"


def test_me_without_a_session_is_refused(client: TestClient) -> None:
    response = client.get("/v1/me")

    assert response.status_code == 401
    assert response.json() == {
        "error": {"code": "not_signed_in", "message": "Sign in to continue."}
    }


def test_signing_up_twice_with_one_email_conflicts(client: TestClient) -> None:
    client.post("/v1/auth/signup", json=SIGN_UP)

    response = client.post("/v1/auth/signup", json=SIGN_UP)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "email_taken"


def test_a_short_password_is_refused(client: TestClient) -> None:
    response = client.post("/v1/auth/signup", json={**SIGN_UP, "password": "short"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "weak_password"


def test_an_invalid_email_gets_the_standard_error_shape(client: TestClient) -> None:
    response = client.post("/v1/auth/signup", json={**SIGN_UP, "email": "not-an-email"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"


def test_sign_in_and_sign_out(client: TestClient) -> None:
    client.post("/v1/auth/signup", json=SIGN_UP)
    client.cookies.clear()

    assert client.post("/v1/auth/login", json=SIGN_IN).status_code == 200
    assert client.get("/v1/me").status_code == 200

    response = client.post("/v1/auth/logout")

    assert response.status_code == 204
    assert client.get("/v1/me").status_code == 401


def test_a_wrong_password_is_refused(client: TestClient) -> None:
    client.post("/v1/auth/signup", json=SIGN_UP)

    response = client.post("/v1/auth/login", json={**SIGN_IN, "password": "wrong password"})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_credentials"


def test_sign_in_attempts_are_rate_limited(make_app: Callable[..., FastAPI]) -> None:
    client = TestClient(make_app(rule="3/minute"))

    codes = [client.post("/v1/auth/login", json=SIGN_IN).status_code for _ in range(4)]

    assert codes == [401, 401, 401, 429]
