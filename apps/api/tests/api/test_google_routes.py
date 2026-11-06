from collections.abc import Callable

from fastapi import FastAPI
from fastapi.testclient import TestClient


def start(client: TestClient) -> str:
    """Begin sign-in and return the state Google would send back."""
    response = client.get("/v1/auth/google/start", follow_redirects=False)
    assert response.status_code == 302
    return response.headers["location"].split("state=")[1]


def test_start_redirects_to_google_and_remembers_the_attempt(client: TestClient) -> None:
    response = client.get("/v1/auth/google/start", follow_redirects=False)

    assert response.headers["location"].startswith("https://accounts.example.com/auth")
    cookie = response.headers["set-cookie"]
    assert cookie.startswith("jalada_google=")
    assert "HttpOnly" in cookie
    assert "Path=/v1/auth/google" in cookie
    assert "Max-Age=600" in cookie


def test_a_good_callback_signs_in_and_goes_home(client: TestClient) -> None:
    state = start(client)

    response = client.get(
        f"/v1/auth/google/callback?code=good-code&state={state}", follow_redirects=False
    )

    assert response.status_code == 302
    assert response.headers["location"] == "http://localhost:3000/"
    assert client.get("/v1/me").json()["display_name"] == "Jane Doe"


def test_taking_over_an_unverified_account_says_the_password_was_removed(
    client: TestClient,
) -> None:
    client.post(
        "/v1/auth/signup",
        json={
            "email": "jane@example.com",
            "password": "correct horse battery",
            "display_name": "Jane",
        },
    )
    state = start(client)

    response = client.get(
        f"/v1/auth/google/callback?code=good-code&state={state}", follow_redirects=False
    )

    assert response.headers["location"] == "http://localhost:3000/?notice=password_removed"


def test_a_callback_with_the_wrong_state_goes_back_to_sign_in(client: TestClient) -> None:
    start(client)

    response = client.get(
        "/v1/auth/google/callback?code=good-code&state=forged", follow_redirects=False
    )

    assert response.headers["location"] == "http://localhost:3000/signin?error=google_failed"
    assert client.get("/v1/me").status_code == 401


def test_a_callback_without_the_attempt_cookie_is_refused(client: TestClient) -> None:
    response = client.get(
        "/v1/auth/google/callback?code=good-code&state=anything", follow_redirects=False
    )

    assert response.headers["location"].endswith("/signin?error=google_failed")


def test_google_refusing_the_code_goes_back_to_sign_in(client: TestClient) -> None:
    state = start(client)

    response = client.get(
        f"/v1/auth/google/callback?code=bad-code&state={state}", follow_redirects=False
    )

    assert response.headers["location"].endswith("/signin?error=google_failed")


def test_start_explains_when_google_is_not_configured(make_app: Callable[..., FastAPI]) -> None:
    client = TestClient(make_app(with_google=False))

    response = client.get("/v1/auth/google/start", follow_redirects=False)

    assert response.headers["location"] == "http://localhost:3000/signin?error=google_unavailable"


def test_sign_in_options_say_when_google_is_on(make_app: Callable[..., FastAPI]) -> None:
    assert TestClient(make_app()).get("/v1/auth/providers").json() == {"google": True}
    assert TestClient(make_app(with_google=False)).get("/v1/auth/providers").json() == {
        "google": False
    }
