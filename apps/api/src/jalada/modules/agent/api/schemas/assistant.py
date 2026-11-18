from datetime import datetime
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, Field

from jalada.modules.agent.application.conversations import ThreadView
from jalada.modules.agent.domain.conversation import MAX_MESSAGE_LENGTH
from jalada.modules.agent.domain.proposals import ProposedAction


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=MAX_MESSAGE_LENGTH)
    # Leave out to start a new conversation.
    thread_id: UUID | None = None


class ThreadSummary(BaseModel):
    id: UUID
    title: str
    updated_at: datetime


class ActionResponse(BaseModel):
    """A change the assistant suggested. Only a tap on Confirm makes it."""

    id: UUID
    kind: Literal["confirm_payment", "change_category"]
    summary: str
    status: Literal["proposed", "confirmed", "declined", "expired"]
    expires_at: datetime

    @classmethod
    def from_action(cls, action: ProposedAction) -> Self:
        return cls(
            id=action.id,
            kind=action.kind,
            summary=action.summary,
            status=action.status,
            expires_at=action.expires_at,
        )


class MessageResponse(BaseModel):
    role: Literal["person", "assistant"]
    text: str
    at: datetime
    # Changes suggested with this answer.
    actions: list[ActionResponse] = Field(default_factory=list)


class ThreadResponse(BaseModel):
    id: UUID
    title: str
    messages: list[MessageResponse]

    @classmethod
    def from_view(cls, view: ThreadView) -> Self:
        by_run: dict[UUID, list[ActionResponse]] = {}
        for action in view.actions:
            by_run.setdefault(action.run_id, []).append(ActionResponse.from_action(action))
        return cls(
            id=view.thread.id,
            title=view.thread.title,
            messages=[
                MessageResponse(
                    role=m.role,
                    text=m.text,
                    at=m.at,
                    actions=by_run.get(m.run_id, []) if m.run_id else [],
                )
                for m in view.messages
            ],
        )
