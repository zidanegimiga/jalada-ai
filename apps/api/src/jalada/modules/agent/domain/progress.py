"""What a turn is doing while the person waits, for the chat to show."""

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum


class Stage(StrEnum):
    THINKING = "thinking"
    LOOKING_UP = "looking_up"
    CHECKING = "checking"


@dataclass(frozen=True)
class Progress:
    stage: Stage
    # For a lookup: the tool's name and what it is doing, in the person's words.
    tool: str | None = None
    label: str | None = None


OnProgress = Callable[[Progress], None]


def ignore(progress: Progress) -> None:
    """For callers that do not show progress."""
