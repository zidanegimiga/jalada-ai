from fastapi.testclient import TestClient


def sign_up(client: TestClient) -> None:
    body = {"email": "jane@example.com", "password": "correct horse battery", "display_name": "J"}
    assert client.post("/v1/auth/signup", json=body).status_code == 201


def test_a_link_code_is_issued_to_the_signed_in_user(client: TestClient) -> None:
    sign_up(client)

    response = client.post("/v1/telegram/link-code").json()

    assert len(response["code"]) == 8
    assert response["bot_link"] is None, "no bot username in the test settings"
    assert client.get("/v1/telegram/status").json() == {"available": False, "linked": False}


def test_linking_needs_a_signed_in_user(client: TestClient) -> None:
    assert client.post("/v1/telegram/link-code").status_code == 401
    assert client.get("/v1/telegram/status").status_code == 401
