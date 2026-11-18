from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

# Long enough for a question, short enough that one message cannot fill a model's context.
MAX_MESSAGE_LENGTH = 2000
TITLE_LENGTH = 80


class Role(StrEnum):
    PERSON = "person"
    ASSISTANT = "assistant"


@dataclass(frozen=True)
class Message:
    role: Role
    text: str
    at: datetime


@dataclass(frozen=True)
class Thread:
    """One conversation. It belongs to one person and only they can read or continue it."""

    id: UUID
    user_id: UUID
    title: str
    created_at: datetime
    updated_at: datetime


def title_from(question: str) -> str:
    """A thread is named after its first question, cut at a word."""
    words = " ".join(question.split())
    if len(words) <= TITLE_LENGTH:
        return words
    return words[:TITLE_LENGTH].rsplit(" ", 1)[0] + "..."
