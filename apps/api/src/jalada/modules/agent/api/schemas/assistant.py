from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from jalada.modules.agent.domain.conversation import MAX_MESSAGE_LENGTH


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=MAX_MESSAGE_LENGTH)
    # Leave out to start a new conversation.
    thread_id: UUID | None = None


class ThreadSummary(BaseModel):
    id: UUID
    title: str
    updated_at: datetime


class MessageResponse(BaseModel):
    role: Literal["person", "assistant"]
    text: str
    at: datetime


class ThreadResponse(BaseModel):
    id: UUID
    title: str
    messages: list[MessageResponse]
