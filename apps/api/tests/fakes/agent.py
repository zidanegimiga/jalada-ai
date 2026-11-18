"""Fakes for the assistant: storage, a stand-in tool, scripted replies and a canned runner."""

import json
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from jalada.modules.agent.application.ports import AgentRun, TurnRequest
from jalada.modules.agent.application.tools import Tool, ToolContext
from jalada.modules.agent.domain.conversation import Message, Thread
from jalada.modules.agent.domain.run import AgentStep, Outcome, StepKind, TurnResult


class FakeThreads:
    def __init__(
        self,
        threads: dict[UUID, Thread],
        messages: list[tuple[UUID, Message]],
        user_id: UUID,
    ) -> None:
        self._threads = threads
        self._messages = messages
        self._user_id = user_id

    def add(self, thread: Thread) -> None:
        if thread.user_id != self._user_id:
            raise ValueError("A thread can only be added for its own user")
        self._threads[thread.id] = thread

    def get(self, thread_id: UUID) -> Thread | None:
        thread = self._threads.get(thread_id)
        return thread if thread is not None and thread.user_id == self._user_id else None

    def recent(self, limit: int) -> list[Thread]:
        mine = [t for t in self._threads.values() if t.user_id == self._user_id]
        return sorted(mine, key=lambda t: t.updated_at, reverse=True)[:limit]

    def touch(self, thread_id: UUID, at: datetime) -> None:
        thread = self.get(thread_id)
        if thread is not None:
            self._threads[thread_id] = Thread(
                thread.id, thread.user_id, thread.title, thread.created_at, at
            )

    def add_message(self, thread_id: UUID, message: Message) -> None:
        if self.get(thread_id) is None:
            raise ValueError("No such thread for this user")
        self._messages.append((thread_id, message))

    def recent_messages(self, thread_id: UUID, limit: int) -> list[Message]:
        if self.get(thread_id) is None:
            return []
        return [m for t, m in self._messages if t == thread_id][-limit:]


class FakeAgentRuns:
    def __init__(self, rows: list[AgentRun]) -> None:
        self.rows = rows

    def add(self, run: AgentRun) -> None:
        self.rows.append(run)

    def for_user(self, user_id: UUID) -> list[AgentRun]:
        return [run for run in self.rows if run.user_id == user_id]


class TotalArguments(BaseModel):
    counterparty: str


class TotalPaid(Tool[TotalArguments]):
    """A stand-in lookup: totals per person, so tests can show one never sees another's."""

    name = "total_paid"
    description = "Total paid to a counterparty."
    arguments = TotalArguments

    def __init__(self, totals: dict[UUID, dict[str, str]]) -> None:
        self.totals = totals
        self.seen: list[UUID] = []

    def run(self, context: ToolContext, arguments: TotalArguments) -> dict[str, Any]:
        self.seen.append(context.user_id)
        mine = self.totals.get(context.user_id, {})
        return {"counterparty": arguments.counterparty, "total": mine.get(arguments.counterparty)}


def use_tool(tool: str, **arguments: Any) -> dict[str, Any]:
    """A model reply asking for a tool."""
    return {"action": "tool", "tool": tool, "arguments": json.dumps(arguments), "answer": None}


def answer(text: str) -> dict[str, Any]:
    """A model reply answering the person."""
    return {"action": "answer", "tool": None, "arguments": None, "answer": text}


class CannedRunner:
    """Answers every turn the same way and remembers what it was asked."""

    def __init__(self, text: str = "You paid Ksh 4,500.", outcome: Outcome = Outcome.ANSWERED):
        self.result = TurnResult(text, outcome, (AgentStep(StepKind.MODEL, "m", "answer", 5),))
        self.requests: list[TurnRequest] = []

    def run(self, request: TurnRequest) -> TurnResult:
        self.requests.append(request)
        return self.result
