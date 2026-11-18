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
    # The turn an answer came from, to show the changes it suggested beside it.
    run_id: UUID | None = None


@dataclass(frozen=True)
class Thread:
    """One conversation. It belongs to one person and only they can read or continue it."""

    id: UUID
    user_id: UUID
    title: str
    created_at: datetime
    updated_at: datetime


def earlier_questions(older: list[Message], limit: int = 10, length: int = 150) -> tuple[str, ...]:
    """What the person asked before the recent messages, newest last, without the answers.

    Enough for "and in October?" to make sense, at a fixed small cost. Old answers are left
    out on purpose: a figure from one is looked up again rather than repeated unchecked.
    """
    asked = [" ".join(m.text.split()) for m in older if m.role == Role.PERSON]
    return tuple(_shorten(text, length) for text in asked[-limit:])


def _shorten(text: str, length: int) -> str:
    if len(text) <= length:
        return text
    return text[:length].rsplit(" ", 1)[0] + "..."


def title_from(question: str) -> str:
    """A thread is named after its first question, cut at a word."""
    words = " ".join(question.split())
    if len(words) <= TITLE_LENGTH:
        return words
    return words[:TITLE_LENGTH].rsplit(" ", 1)[0] + "..."
