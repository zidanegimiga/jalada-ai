"""The assistant in a chat app, such as Telegram now and WhatsApp later.

A chat app is a ReplyChannel: it can send an answer with its suggested changes as buttons, and
send a short note. Each app is one adapter; nothing here knows which app it is.

Questions are answered on the job queue, because a turn can take longer than a chat app waits
for its webhook to return, and a queued question survives a restart. Taps on the buttons are
quick and are answered at once.
"""

import logging
from collections.abc import Callable, Sequence
from datetime import timedelta
from typing import Any, Protocol
from uuid import UUID

from jalada.core.ports import Clock
from jalada.modules.agent.application.confirmations import ActionConfirmations
from jalada.modules.agent.application.conversations import Conversations
from jalada.modules.agent.domain.proposals import ActionStatus, ProposedAction
from jalada.shared.errors import ActionClosed, ActionNotFound, ApplicationError, InvalidEntry
from jalada.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)

ANSWER_QUESTION_JOB = "answer_question"
# A question within this long of the last one continues the same conversation.
CONTINUE_WITHIN = timedelta(minutes=30)

NOTES = {
    "failed": "Something went wrong answering that. Please ask again in a little while.",
    "gone": "That change was already decided, or it has expired. Ask again if you still want it.",
    "missing": "I could not find that change.",
}


class ReplyChannel(Protocol):
    """How the assistant answers in one chat app. `chat` is the app's own address."""

    def answer(self, chat: str, text: str, actions: Sequence[ProposedAction]) -> None: ...
    def note(self, chat: str, text: str) -> None: ...


class ChannelAssistant:
    """Asking and deciding from a chat app, for a person the app has already identified."""

    def __init__(
        self,
        unit_of_work: Callable[[], UnitOfWork],
        conversations: Conversations,
        confirmations: ActionConfirmations,
        channel: ReplyChannel,
        clock: Clock,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._conversations = conversations
        self._confirmations = confirmations
        self._channel = channel
        self._clock = clock

    def queue(self, user_id: UUID, chat: str, question: str) -> None:
        """Keeps the question for the worker to answer."""
        with self._unit_of_work() as work:
            work.jobs.enqueue(
                ANSWER_QUESTION_JOB,
                {"user_id": str(user_id), "chat": chat, "question": question},
            )
            work.commit()

    def answer(self, user_id: UUID, chat: str, question: str) -> None:
        """Runs the turn and replies. Never raises: a failure is told to the person instead,
        so the job is not tried again and the question not asked twice."""
        try:
            reply = self._conversations.ask(user_id, question, self._recent_thread(user_id))
            waiting = [a for a in reply.actions if a.status == ActionStatus.PROPOSED]
            self._channel.answer(chat, reply.text, waiting)
        except Exception:
            logger.exception("Answering a chat question failed")
            self._note(chat, NOTES["failed"])

    def decide(self, user_id: UUID, chat: str, action_id: UUID, confirm: bool) -> None:
        try:
            if confirm:
                action = self._confirmations.confirm(user_id, action_id)
                self._note(chat, f"Done: {action.summary}")
            else:
                action = self._confirmations.decline(user_id, action_id)
                self._note(chat, f"Left as it was: {action.summary}")
        except ActionClosed:
            self._note(chat, NOTES["gone"])
        except ActionNotFound:
            self._note(chat, NOTES["missing"])
        except InvalidEntry as problem:
            self._note(chat, problem.reason)
        except ApplicationError:
            self._note(chat, NOTES["failed"])

    def _recent_thread(self, user_id: UUID) -> UUID | None:
        latest = self._conversations.threads(user_id, limit=1)
        if latest and self._clock.now() - latest[0].updated_at < CONTINUE_WITHIN:
            return latest[0].id
        return None

    def _note(self, chat: str, text: str) -> None:
        try:
            self._channel.note(chat, text)
        except Exception as error:
            logger.warning("Replying in the chat failed with %s", type(error).__name__)


class AnswerQuestionJob:
    """The worker's side: answers a question kept by ChannelAssistant.queue."""

    def __init__(self, assistant: ChannelAssistant) -> None:
        self._assistant = assistant

    def handle(self, payload: dict[str, Any]) -> None:
        self._assistant.answer(UUID(payload["user_id"]), payload["chat"], payload["question"])

    def give_up(self, payload: dict[str, Any]) -> None:
        pass
