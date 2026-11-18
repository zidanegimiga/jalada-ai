from collections.abc import Sequence

from jalada.modules.agent.domain.proposals import ProposedAction
from jalada.modules.telegram.application.ports import ChatChannel
from jalada.modules.telegram.application.telegram_capture import TAP_PREFIX


class TelegramReplies:
    """The assistant's answers in Telegram: the answer, then each suggested change on its own
    message with Confirm and Not now buttons."""

    def __init__(self, bot: ChatChannel) -> None:
        self._bot = bot

    def answer(self, chat: str, text: str, actions: Sequence[ProposedAction]) -> None:
        self._bot.send(int(chat), text)
        for action in actions:
            self._bot.send_with_buttons(
                int(chat),
                action.summary,
                [
                    ("Confirm", f"{TAP_PREFIX}confirm:{action.id}"),
                    ("Not now", f"{TAP_PREFIX}decline:{action.id}"),
                ],
            )

    def note(self, chat: str, text: str) -> None:
        self._bot.send(int(chat), text)
