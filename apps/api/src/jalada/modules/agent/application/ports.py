from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol
from uuid import UUID

from jalada.modules.agent.domain.conversation import Message, Thread
from jalada.modules.agent.domain.progress import OnProgress, ignore
from jalada.modules.agent.domain.proposals import ProposedAction
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
    def recent(self, limit: int) -> list[Thread]:
        """The threads most recently used first."""
        ...

    def touch(self, thread_id: UUID, at: datetime) -> None: ...
    def add_message(self, thread_id: UUID, message: Message) -> None: ...
    def recent_messages(self, thread_id: UUID, limit: int) -> list[Message]:
        """The last `limit` messages, oldest first."""
        ...


class AgentRunRepository(Protocol):
    def add(self, run: AgentRun) -> None: ...
    def for_user(self, user_id: UUID) -> list[AgentRun]: ...


class ActionRepository(Protocol):
    """One person's suggested changes. Another person's are never found."""

    def add(self, action: ProposedAction) -> None: ...
    def get(self, action_id: UUID) -> ProposedAction | None: ...
    def save(self, action: ProposedAction) -> None:
        """Stores a decision on an action that is already there."""
        ...

    def for_run(self, run_id: UUID) -> list[ProposedAction]: ...
    def for_thread(self, thread_id: UUID) -> list[ProposedAction]: ...


class TurnTracer(Protocol):
    """Sends what a turn did to a tracing service. Never what was asked or answered."""

    def record(self, run: AgentRun) -> None: ...


class NoTracing:
    def record(self, run: AgentRun) -> None:
        pass


@dataclass(frozen=True)
class TurnRequest:
    """What a runner gets for one turn. The user id is for tools, never for the model."""

    run_id: UUID
    user_id: UUID
    question: str
    history: tuple[Message, ...]
    today: date
    # The conversation, so a suggested change can be shown in it.
    thread_id: UUID | None = None


class AgentRunner(Protocol):
    """Runs one turn: looks things up as needed, then answers within the budget."""

    def run(self, request: TurnRequest, on_progress: OnProgress = ignore) -> TurnResult: ...
