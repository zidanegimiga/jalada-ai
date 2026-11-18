from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol
from uuid import UUID

from jalada.modules.agent.domain.conversation import Message, Thread
from jalada.modules.agent.domain.run import AgentStep, Outcome, TurnResult


@dataclass(frozen=True)
class AgentRun:
    """One turn: the person's question to the reply, with every step it took."""

    id: UUID
    user_id: UUID
    thread_id: UUID
    outcome: Outcome
    steps: tuple[AgentStep, ...]
    started_at: datetime
    finished_at: datetime


class ThreadRepository(Protocol):
    """One person's conversations. Another person's threads are never found."""

    def add(self, thread: Thread) -> None: ...
    def get(self, thread_id: UUID) -> Thread | None: ...
    def touch(self, thread_id: UUID, at: datetime) -> None: ...
    def add_message(self, thread_id: UUID, message: Message) -> None: ...
    def recent_messages(self, thread_id: UUID, limit: int) -> list[Message]:
        """The last `limit` messages, oldest first."""
        ...


class AgentRunRepository(Protocol):
    def add(self, run: AgentRun) -> None: ...
    def for_user(self, user_id: UUID) -> list[AgentRun]: ...


@dataclass(frozen=True)
class TurnRequest:
    """What a runner gets for one turn. The user id is for tools, never for the model."""

    run_id: UUID
    user_id: UUID
    question: str
    history: tuple[Message, ...]
    today: date


class AgentRunner(Protocol):
    """Runs one turn: looks things up as needed, then answers within the budget."""

    def run(self, request: TurnRequest) -> TurnResult: ...
