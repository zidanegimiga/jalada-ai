from collections.abc import Callable
from datetime import timedelta

import pytest
from fakes import FakeIdempotencyStore, FixedClock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from samples import MPESA

from jalada.core.idempotency.requests import IdempotentRequests
from jalada.shared.http.idempotency import MAX_BODY_BYTES


class Counter:
    """A write route that counts how often it really ran."""

    def __init__(self) -> None:
        self.runs = 0
        self.fail = False

    def __call__(self) -> dict[str, int]:
        if self.fail:
            raise RuntimeError("database went away")
        self.runs += 1
        return {"runs": self.runs}


@pytest.fixture
def counter() -> Counter:
    return Counter()


@pytest.fixture
def kept() -> FakeIdempotencyStore:
    return FakeIdempotencyStore()


@pytest.fixture
def app(
    make_app: Callable[..., FastAPI],
    kept: FakeIdempotencyStore,
    clock: FixedClock,
    counter: Counter,
) -> FastAPI:
    built = make_app(idempotency=IdempotentRequests(kept, clock))
    built.add_api_route("/v1/count", counter, methods=["POST"])
    built.add_api_route("/v1/count", counter, methods=["GET"])
    return built


def signed_in(app: FastAPI, email: str = "jane@example.com") -> TestClient:
    client = TestClient(app, raise_server_exceptions=False)
    body = {"email": email, "password": "correct horse battery", "display_name": "Jane"}
    assert client.post("/v1/auth/signup", json=body).status_code == 201
    return client


def send(client: TestClient, key: str, body: object = None) -> dict[str, object]:
    response = client.post("/v1/count", json=body, headers={"Idempotency-Key": key})
    return {
        "status": response.status_code,
        "body": response.json() if response.status_code < 500 else response.text,
        "replayed": response.headers.get("idempotent-replayed"),
    }


def test_a_retry_gets_the_first_answer_without_running_again(
    app: FastAPI, counter: Counter
) -> None:
    client = signed_in(app)

    first = send(client, "change-1")
    again = send(client, "change-1")

    assert first == {"status": 200, "body": {"runs": 1}, "replayed": None}
    assert again == {"status": 200, "body": {"runs": 1}, "replayed": "true"}
    assert counter.runs == 1


def test_a_replayed_answer_still_gets_a_request_id(app: FastAPI) -> None:
    client = signed_in(app)
    send(client, "change-1")

    again = client.post("/v1/count", headers={"Idempotency-Key": "change-1"})

    assert len(again.headers["x-request-id"]) == 32


def test_each_key_runs_once(app: FastAPI, counter: Counter) -> None:
    client = signed_in(app)

    send(client, "change-1")
    send(client, "change-2")

    assert counter.runs == 2


def test_the_same_key_for_a_different_request_is_refused(app: FastAPI, counter: Counter) -> None:
    client = signed_in(app)
    send(client, "change-1", {"amount": 100})

    reused = send(client, "change-1", {"amount": 900})

    assert reused["status"] == 422
    assert reused["body"] == {
        "error": {
            "code": "idempotency_key_reused",
            "message": "That Idempotency-Key was already used for a different request.",
        }
    }
    assert counter.runs == 1


def test_a_retry_while_the_first_is_still_running_is_told_to_wait(
    app: FastAPI, kept: FakeIdempotencyStore, clock: FixedClock
) -> None:
    client = signed_in(app)
    send(client, "change-1")
    # As if the first try had only just started.
    [entry] = kept.kept.values()
    entry.answer = None

    assert send(client, "change-1")["status"] == 409


def test_a_first_try_that_never_finished_is_run_again(
    app: FastAPI, kept: FakeIdempotencyStore, clock: FixedClock, counter: Counter
) -> None:
    client = signed_in(app)
    send(client, "change-1")
    [entry] = kept.kept.values()
    entry.answer = None
    clock.current += timedelta(minutes=3)

    assert send(client, "change-1")["body"] == {"runs": 2}


def test_answers_are_kept_for_a_day(app: FastAPI, clock: FixedClock, counter: Counter) -> None:
    client = signed_in(app)
    send(client, "change-1")

    clock.current += timedelta(hours=23)
    assert send(client, "change-1")["replayed"] == "true"
    clock.current += timedelta(hours=2)
    assert send(client, "change-1")["replayed"] is None
    assert counter.runs == 2


def test_a_server_failure_is_not_kept_so_the_retry_runs(app: FastAPI, counter: Counter) -> None:
    client = signed_in(app)
    counter.fail = True
    assert send(client, "change-1")["status"] == 500

    counter.fail = False
    assert send(client, "change-1") == {"status": 200, "body": {"runs": 1}, "replayed": None}


def test_keys_belong_to_one_session(app: FastAPI, counter: Counter) -> None:
    jane = signed_in(app)
    other = signed_in(app, "other@example.com")

    send(jane, "change-1")
    theirs = send(other, "change-1")

    assert theirs["body"] == {"runs": 2}


def test_requests_without_a_key_or_session_or_that_only_read_run_every_time(
    app: FastAPI, counter: Counter
) -> None:
    client = signed_in(app)
    client.post("/v1/count")
    client.post("/v1/count")
    client.get("/v1/count", headers={"Idempotency-Key": "change-1"})
    client.get("/v1/count", headers={"Idempotency-Key": "change-1"})
    TestClient(app).post("/v1/count", headers={"Idempotency-Key": "change-1"})

    assert counter.runs == 5


def test_keys_must_be_short_and_plain(app: FastAPI, counter: Counter) -> None:
    client = signed_in(app)

    assert send(client, "a" * 65)["status"] == 400
    assert send(client, "has space")["status"] == 400
    assert counter.runs == 0


def test_keyed_bodies_are_held_to_the_upload_limit(app: FastAPI, counter: Counter) -> None:
    client = signed_in(app)
    too_big = b"x" * (MAX_BODY_BYTES + 1)

    response = client.post("/v1/count", content=too_big, headers={"Idempotency-Key": "big"})

    assert response.status_code == 413
    assert counter.runs == 0


def test_the_desktop_sends_its_session_as_a_bearer_token(app: FastAPI, counter: Counter) -> None:
    client = signed_in(app)
    token = client.cookies["jalada_session"]
    desktop = TestClient(app)
    headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": "change-1"}

    desktop.post("/v1/count", headers=headers)
    again = desktop.post("/v1/count", headers=headers)

    assert again.headers["idempotent-replayed"] == "true"
    assert counter.runs == 1


def test_a_pasted_message_sent_twice_is_saved_once(app: FastAPI) -> None:
    client = signed_in(app)
    headers = {"Idempotency-Key": "paste-1"}

    first = client.post("/v1/evidence/text", json={"text": MPESA}, headers=headers)
    again = client.post("/v1/evidence/text", json={"text": MPESA}, headers=headers)

    assert first.status_code == again.status_code
    assert again.json() == first.json()
    assert again.headers["idempotent-replayed"] == "true"
    assert len(client.get("/v1/evidence").json()["items"]) == 1
