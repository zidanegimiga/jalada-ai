import secrets

from fastapi.testclient import TestClient

from jalada.modules.accounts.domain.device_codes import challenge_for

SIGN_UP = {"email": "jane@example.com", "password": "correct horse battery", "display_name": "Jane"}
VERIFIER = secrets.token_urlsafe(48)


def browser_code(client: TestClient) -> str:
    """What the web app does once the signed-in person allows the desktop app in."""
    client.post("/v1/auth/signup", json=SIGN_UP)
    response = client.post("/v1/auth/device/codes", json={"challenge": challenge_for(VERIFIER)})
    assert response.status_code == 201
    code: str = response.json()["code"]
    return code


def test_the_desktop_app_signs_in_with_the_code_and_its_verifier(client: TestClient) -> None:
    code = browser_code(client)
    client.cookies.clear()

    response = client.post("/v1/auth/device/token", json={"code": code, "verifier": VERIFIER})

    assert response.status_code == 200
    body = response.json()
    assert body["user"]["display_name"] == "Jane"
    assert "set-cookie" not in response.headers


def test_the_desktop_session_works_as_a_bearer_token(client: TestClient) -> None:
    code = browser_code(client)
    client.cookies.clear()
    token = client.post("/v1/auth/device/token", json={"code": code, "verifier": VERIFIER}).json()[
        "token"
    ]

    me = client.get("/v1/me", headers={"Authorization": f"Bearer {token}"})

    assert me.status_code == 200
    assert me.json()["email"] == "jane@example.com"


def test_signing_out_ends_a_bearer_session(client: TestClient) -> None:
    code = browser_code(client)
    client.cookies.clear()
    token = client.post("/v1/auth/device/token", json={"code": code, "verifier": VERIFIER}).json()[
        "token"
    ]
    bearer = {"Authorization": f"Bearer {token}"}

    client.post("/v1/auth/logout", headers=bearer)

    assert client.get("/v1/me", headers=bearer).status_code == 401


def test_a_wrong_verifier_gets_a_clear_error(client: TestClient) -> None:
    code = browser_code(client)

    response = client.post(
        "/v1/auth/device/token",
        json={"code": code, "verifier": secrets.token_urlsafe(48)},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "device_sign_in_failed"


def test_only_a_signed_in_person_can_ask_for_a_code(client: TestClient) -> None:
    response = client.post("/v1/auth/device/codes", json={"challenge": challenge_for(VERIFIER)})

    assert response.status_code == 401


def test_other_authorization_schemes_are_ignored(client: TestClient) -> None:
    response = client.get("/v1/me", headers={"Authorization": "Basic amFuZTpwYXNz"})

    assert response.status_code == 401
