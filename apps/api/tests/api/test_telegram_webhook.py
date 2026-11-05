from collections.abc import Callable
from typing import Any

from fakes import FakeChat
from fastapi import FastAPI
from fastapi.testclient import TestClient

UPDATE: dict[str, Any] = {
    "update_id": 1,
    "message": {"from": {"id": 1}, "chat": {"id": 2}, "text": "/start"},
}


def post(client: TestClient, secret: str | None) -> int:
    headers = {"X-Telegram-Bot-Api-Secret-Token": secret} if secret else {}
    return client.post("/v1/telegram/webhook", json=UPDATE, headers=headers).status_code


def test_updates_with_the_right_secret_are_handled(client: TestClient, chat: FakeChat) -> None:
    assert post(client, "hook-secret") == 200
    assert len(chat.sent) == 1


def test_updates_without_the_secret_are_refused(client: TestClient, chat: FakeChat) -> None:
    assert post(client, None) == 401
    assert post(client, "guess") == 401
    assert chat.sent == []


def test_the_webhook_does_not_exist_without_a_bot(make_app: Callable[..., FastAPI]) -> None:
    assert post(TestClient(make_app(with_telegram=False)), "hook-secret") == 404


def test_the_webhook_is_not_in_the_public_api_description(client: TestClient) -> None:
    assert "/v1/telegram/webhook" not in client.get("/openapi.json").json()["paths"]
