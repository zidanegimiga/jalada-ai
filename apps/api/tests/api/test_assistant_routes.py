import json
import uuid
from collections.abc import Callable
from datetime import date
from typing import Any

import pytest
from fakes import FakeUnitOfWork, FixedClock, Store
from fakes.agent import CannedRunner
from fastapi import FastAPI
from fastapi.testclient import TestClient
from samples import confirmed_entry

from jalada.modules.agent.application.conversations import Conversations
from jalada.modules.agent.application.ports import TurnRequest
from jalada.modules.agent.application.proposals import ActionProposals
from jalada.modules.agent.application.tools import ToolContext
from jalada.modules.agent.domain.progress import OnProgress, ignore
from jalada.modules.agent.domain.proposals import ActionKind
from jalada.modules.agent.domain.run import TurnResult
from jalada.modules.agent.wiring import build_confirmations
from jalada.modules.ledger.application.entry_review import EntryReview


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


class SuggestingRunner(CannedRunner):
    """Suggests moving the person's first payment to Workspace rent, as a model would."""

    def __init__(self, store: Store, proposals: ActionProposals) -> None:
        super().__init__("I suggested moving it to Workspace rent. Tap Confirm to change it.")
        self.store = store
        self.proposals = proposals

    def run(self, request: TurnRequest, on_progress: OnProgress = ignore) -> TurnResult:
        [payment] = [t for t in self.store.transactions.values() if t.user_id == request.user_id]
        context = ToolContext(request.user_id, request.today, request.run_id, request.thread_id)
        payload = {"entry_id": str(payment.id), "category": "business_rent"}
        self.proposals.propose(context, ActionKind.CHANGE_CATEGORY, payload, "Move it to rent")
        return super().run(request, on_progress)


@pytest.fixture
def suggesting(make_app: Callable[..., FastAPI], store: Store) -> TestClient:
    def work() -> FakeUnitOfWork:
        return FakeUnitOfWork(store)

    clock = FixedClock()
    runner = SuggestingRunner(store, ActionProposals(work, clock))
    app = make_app(
        assistant=Conversations(work, runner, clock),
        assistant_actions=build_confirmations(work, clock, EntryReview(work, clock)),
    )
    client = TestClient(app)
    sign_up(client)
    user = next(iter(store.users))
    store.save_entries(confirmed_entry(user, date(2026, 7, 4), 250_000, "out", "business_other"))
    return client


def suggested(client: TestClient) -> dict[str, Any]:
    [(_, answer)] = [
        e
        for e in events(
            client.post("/v1/assistant/messages", json={"question": "That was rent"}).text
        )
        if e[0] == "answer"
    ]
    return answer


def test_a_suggested_change_comes_with_the_answer_and_in_the_thread(
    suggesting: TestClient,
) -> None:
    answer = suggested(suggesting)

    [action] = answer["actions"]
    assert (action["summary"], action["status"], action["kind"]) == (
        "Move it to rent",
        "proposed",
        "change_category",
    )
    thread = suggesting.get(f"/v1/assistant/threads/{answer['thread_id']}").json()
    assert thread["messages"][0]["actions"] == []
    assert thread["messages"][1]["actions"] == [action]


def test_confirming_over_the_api_changes_the_payment(suggesting: TestClient, store: Store) -> None:
    action = suggested(suggesting)["actions"][0]

    confirmed = suggesting.post(f"/v1/assistant/actions/{action['id']}/confirm")

    assert (confirmed.status_code, confirmed.json()["status"]) == (200, "confirmed")
    [payment] = store.transactions.values()
    assert payment.lines[0].category == "business_rent"
    again = suggesting.post(f"/v1/assistant/actions/{action['id']}/confirm")
    assert (again.status_code, again.json()["error"]["code"]) == (409, "already_decided")


def test_declining_over_the_api_changes_nothing(suggesting: TestClient, store: Store) -> None:
    action = suggested(suggesting)["actions"][0]

    declined = suggesting.post(f"/v1/assistant/actions/{action['id']}/decline")

    assert declined.json()["status"] == "declined"
    [payment] = store.transactions.values()
    assert payment.lines[0].category == "business_other"


def test_an_unknown_suggestion_is_not_found(suggesting: TestClient) -> None:
    response = suggesting.post(f"/v1/assistant/actions/{uuid.uuid4()}/confirm")

    assert response.status_code == 404
