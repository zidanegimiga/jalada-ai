from typing import Any
from uuid import UUID

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from jalada.dependencies import CurrentUser, ServicesDependency
from jalada.modules.agent.api.events import stream_turn
from jalada.modules.agent.api.schemas.assistant import (
    MessageResponse,
    QuestionRequest,
    ThreadResponse,
    ThreadSummary,
)
from jalada.modules.agent.application.conversations import Conversations
from jalada.services import Services
from jalada.shared.errors import AssistantOff, EmptyQuestion
from jalada.shared.http.errors import TooManyAttempts

router = APIRouter(tags=["assistant"])

EVENT_STREAM: dict[int | str, dict[str, Any]] = {
    200: {
        "description": "Server-sent events: progress, then answer or error.",
        "content": {"text/event-stream": {"schema": {"type": "string"}}},
    }
}


def _assistant(services: Services) -> Conversations:
    if services.conversations is None:
        raise AssistantOff
    return services.conversations


@router.get("/v1/assistant/threads")
def list_threads(user: CurrentUser, services: ServicesDependency) -> list[ThreadSummary]:
    threads = _assistant(services).threads(user.id)
    return [ThreadSummary(id=t.id, title=t.title, updated_at=t.updated_at) for t in threads]


@router.get("/v1/assistant/threads/{thread_id}")
def read_thread(thread_id: UUID, user: CurrentUser, services: ServicesDependency) -> ThreadResponse:
    view = _assistant(services).thread(user.id, thread_id)
    return ThreadResponse(
        id=view.thread.id,
        title=view.thread.title,
        messages=[MessageResponse(role=m.role, text=m.text, at=m.at) for m in view.messages],
    )


@router.post("/v1/assistant/messages", response_class=StreamingResponse, responses=EVENT_STREAM)
def ask_assistant(
    request: QuestionRequest, user: CurrentUser, services: ServicesDependency
) -> StreamingResponse:
    """Ask a question, in a new conversation or an earlier one, and follow the answer."""
    assistant = _assistant(services)
    if not request.question.strip():
        raise EmptyQuestion
    if not services.assistant_limiter.allow(f"assistant:{user.id}"):
        raise TooManyAttempts
    if request.thread_id is not None:
        # Raises ThreadNotFound before the stream starts, so it comes back as a plain 404.
        assistant.thread(user.id, request.thread_id)
    turns = stream_turn(
        lambda on_progress: assistant.ask(user.id, request.question, request.thread_id, on_progress)
    )
    return StreamingResponse(
        turns,
        media_type="text/event-stream",
        # no-transform stops proxies that compress, the web app's included, from holding
        # events back until the stream ends. X-Accel-Buffering does the same for nginx.
        headers={"Cache-Control": "no-store, no-transform", "X-Accel-Buffering": "no"},
    )
