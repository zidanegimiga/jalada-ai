from collections.abc import Callable
from dataclasses import dataclass
from uuid import UUID, uuid4

from jalada.core.ports import Clock
from jalada.modules.agent.application.ports import AgentRun, AgentRunner, TurnRequest
from jalada.modules.agent.domain.conversation import (
    MAX_MESSAGE_LENGTH,
    Message,
    Role,
    Thread,
    title_from,
)
from jalada.modules.agent.domain.run import Outcome
from jalada.shared.errors import EmptyQuestion, ThreadNotFound
from jalada.unit_of_work import UnitOfWork

# Earlier messages sent with each question. Older ones are left out for now.
HISTORY_MESSAGES = 10
# How much of a conversation is shown when it is opened again.
SHOWN_MESSAGES = 200


@dataclass(frozen=True)
class Reply:
    thread_id: UUID
    text: str
    outcome: Outcome


@dataclass(frozen=True)
class ThreadView:
    thread: Thread
    messages: list[Message]


class Conversations:
    """Asking the assistant: keeps the thread, runs the turn and records what it did."""

    def __init__(
        self,
        unit_of_work: Callable[[], UnitOfWork],
        runner: AgentRunner,
        clock: Clock,
        new_id: Callable[[], UUID] = uuid4,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._runner = runner
        self._clock = clock
        self._new_id = new_id

    def threads(self, user_id: UUID, limit: int = 50) -> list[Thread]:
        with self._unit_of_work() as work:
            return work.agent_threads_for(user_id).recent(limit)

    def thread(self, user_id: UUID, thread_id: UUID) -> ThreadView:
        with self._unit_of_work() as work:
            threads = work.agent_threads_for(user_id)
            thread = threads.get(thread_id)
            if thread is None:
                raise ThreadNotFound
            return ThreadView(thread, threads.recent_messages(thread_id, SHOWN_MESSAGES))

    def ask(self, user_id: UUID, question: str, thread_id: UUID | None = None) -> Reply:
        question = question.strip()[:MAX_MESSAGE_LENGTH]
        if not question:
            raise EmptyQuestion
        started = self._clock.now()
        with self._unit_of_work() as work:
            threads = work.agent_threads_for(user_id)
            if thread_id is None:
                thread = Thread(self._new_id(), user_id, title_from(question), started, started)
                threads.add(thread)
            else:
                found = threads.get(thread_id)
                if found is None:
                    raise ThreadNotFound
                thread = found
            history = threads.recent_messages(thread.id, HISTORY_MESSAGES)
            threads.add_message(thread.id, Message(Role.PERSON, question, started))
            work.commit()

        run_id = self._new_id()
        request = TurnRequest(run_id, user_id, question, tuple(history), started.date())
        result = self._runner.run(request)

        finished = self._clock.now()
        with self._unit_of_work() as work:
            threads = work.agent_threads_for(user_id)
            threads.add_message(thread.id, Message(Role.ASSISTANT, result.text, finished))
            threads.touch(thread.id, finished)
            work.agent_runs.add(
                AgentRun(
                    run_id, user_id, thread.id, result.outcome, result.steps, started, finished
                )
            )
            work.commit()
        return Reply(thread.id, result.text, result.outcome)
