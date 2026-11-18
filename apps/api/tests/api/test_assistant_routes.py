import json
from collections.abc import Callable
from typing import Any

import pytest
from fakes import FakeUnitOfWork, FixedClock, Store
from fakes.agent import CannedRunner
from fastapi import FastAPI
from fastapi.testclient import TestClient

from jalada.modules.agent.application.conversations import Conversations
from jalada.modules.agent.application.ports import TurnRequest
from jalada.modules.agent.domain.progress import OnProgress, ignore
from jalada.modules.agent.domain.run import TurnResult


def sign_up(client: TestClient, email: str = "jane@example.com") -> None:
    body = {"email": email, "password": "correct horse battery", "display_name": "J"}
    assert client.post("/v1/auth/signup", json=body).status_code == 201


def events(body: str) -> list[tuple[str, dict[str, Any]]]:
    """The server-sent events in a response body, as (name, data)."""
    found = []
    for block in body.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.splitlines())
        found.append((lines["event"], json.loads(lines["data"])))
    return found


@pytest.fixture
def assistant(store: Store) -> Conversations:
    return Conversations(lambda: FakeUnitOfWork(store), CannedRunner(), FixedClock())


@pytest.fixture
def signed_in(make_app: Callable[..., FastAPI], assistant: Conversations) -> TestClient:
    client = TestClient(make_app(assistant=assistant))
    sign_up(client)
    return client


def test_a_question_streams_progress_then_the_answer(signed_in: TestClient) -> None:
    response = signed_in.post("/v1/assistant/messages", json={"question": "How much to KPLC?"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    # Without no-transform the web app gzips the stream and holds every event to the end.
    assert "no-transform" in response.headers["cache-control"]
    [(first, progress), (last, answer)] = events(response.text)
    assert (first, progress["stage"]) == ("progress", "thinking")
    assert last == "answer"
    assert (answer["text"], answer["outcome"]) == ("You paid Ksh 4,500.", "answered")


def test_the_conversation_can_be_listed_opened_and_continued(signed_in: TestClient) -> None:
    first = events(signed_in.post("/v1/assistant/messages", json={"question": "KPLC?"}).text)
    thread_id = first[-1][1]["thread_id"]

    signed_in.post("/v1/assistant/messages", json={"question": "And rent?", "thread_id": thread_id})

    [summary] = signed_in.get("/v1/assistant/threads").json()
    assert (summary["id"], summary["title"]) == (thread_id, "KPLC?")
    thread = signed_in.get(f"/v1/assistant/threads/{thread_id}").json()
    assert [(m["role"], m["text"]) for m in thread["messages"]] == [
        ("person", "KPLC?"),
        ("assistant", "You paid Ksh 4,500."),
        ("person", "And rent?"),
        ("assistant", "You paid Ksh 4,500."),
    ]


def test_another_persons_conversation_is_not_found(
    make_app: Callable[..., FastAPI], assistant: Conversations
) -> None:
    app = make_app(assistant=assistant)
    owner, other = TestClient(app), TestClient(app)
    sign_up(owner)
    sign_up(other, "other@example.com")
    thread_id = events(owner.post("/v1/assistant/messages", json={"question": "KPLC?"}).text)[-1][
        1
    ]["thread_id"]

    assert other.get(f"/v1/assistant/threads/{thread_id}").status_code == 404
    continued = other.post(
        "/v1/assistant/messages", json={"question": "Hi", "thread_id": thread_id}
    )
    assert continued.status_code == 404
    assert other.get("/v1/assistant/threads").json() == []


def test_the_assistant_needs_a_signed_in_person(
    make_app: Callable[..., FastAPI], assistant: Conversations
) -> None:
    client = TestClient(make_app(assistant=assistant))

    assert client.post("/v1/assistant/messages", json={"question": "Hi"}).status_code == 401
    assert client.get("/v1/assistant/threads").status_code == 401


def test_the_assistant_is_not_found_when_switched_off(client: TestClient) -> None:
    sign_up(client)

    response = client.post("/v1/assistant/messages", json={"question": "Hi"})

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "assistant_off"


@pytest.mark.parametrize("question", ["", "   ", "x" * 2001])
def test_empty_or_long_questions_are_refused(signed_in: TestClient, question: str) -> None:
    assert signed_in.post("/v1/assistant/messages", json={"question": question}).status_code == 422


def test_questions_are_limited_per_person(
    make_app: Callable[..., FastAPI], assistant: Conversations
) -> None:
    client = TestClient(make_app(assistant=assistant, assistant_rule="2/hour"))
    sign_up(client)

    codes = [
        client.post("/v1/assistant/messages", json={"question": "Hi"}).status_code for _ in range(3)
    ]

    assert codes == [200, 200, 429]


def test_a_failed_turn_ends_with_an_error_event_and_no_details(
    make_app: Callable[..., FastAPI], store: Store
) -> None:
    class Broken(CannedRunner):
        def run(self, request: TurnRequest, on_progress: OnProgress = ignore) -> TurnResult:
            raise RuntimeError("database at 10.0.0.5 said no for 0712345678")

    client = TestClient(
        make_app(assistant=Conversations(lambda: FakeUnitOfWork(store), Broken(), FixedClock()))
    )
    sign_up(client)

    [(name, data)] = events(client.post("/v1/assistant/messages", json={"question": "Hi"}).text)

    assert (name, data["code"]) == ("error", "assistant_failed")
    assert "0712345678" not in json.dumps(data)
