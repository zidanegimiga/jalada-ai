"""What the model may decide to do next in a turn."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ToolCall:
    """Look something up. Arguments are checked against the tool before it runs."""

    tool: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Answer:
    """Reply to the person. The figures in it are checked before it is sent."""

    text: str


Decision = ToolCall | Answer
