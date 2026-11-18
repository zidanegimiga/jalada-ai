"""Tools the assistant can use, and the registry it picks them from."""

from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import date
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ValidationError


@dataclass(frozen=True)
class ToolContext:
    """Set by the app for each turn. The model never sees or chooses these."""

    user_id: UUID
    today: date
    # Where a suggested change belongs. Set during a turn; lookups do not need them.
    run_id: UUID | None = None
    thread_id: UUID | None = None


class BadArguments(Exception):
    """The model asked for a tool with arguments that do not fit it."""


class Tool[A: BaseModel](ABC):
    """A lookup over the person's records, with typed arguments that never include a user."""

    name: str
    description: str
    arguments: type[A]
    # Shown in the chat while the tool runs.
    label: str = "Looking it up"

    @abstractmethod
    def run(self, context: ToolContext, arguments: A) -> dict[str, Any]:
        """Only the fields an answer needs: tool results are sent to the model."""

    def parse(self, raw: dict[str, Any]) -> A:
        try:
            return self.arguments.model_validate(raw)
        except ValidationError as error:
            fields = ", ".join(".".join(map(str, e["loc"])) or "arguments" for e in error.errors())
            raise BadArguments(f"{self.name} arguments do not fit: {fields}") from None

    def call(self, context: ToolContext, raw: dict[str, Any]) -> dict[str, Any]:
        return self.run(context, self.parse(raw))


class ToolRegistry:
    def __init__(self, tools: Iterable[Tool[Any]]) -> None:
        self._tools = {tool.name: tool for tool in tools}

    def get(self, name: str) -> Tool[Any] | None:
        return self._tools.get(name)

    def __iter__(self) -> Iterator[Tool[Any]]:
        return iter(self._tools.values())
