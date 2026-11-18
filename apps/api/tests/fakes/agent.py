"""Fake storage for the assistant's conversations and runs."""

from datetime import datetime
from uuid import UUID

from jalada.modules.agent.application.ports import AgentRun
from jalada.modules.agent.domain.conversation import Message, Thread


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
