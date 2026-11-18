"""Builds the Telegram module's use cases from the pieces the composition root shares."""

from collections.abc import Callable

from jalada.core.ports import Clock, Limiter
from jalada.modules.evidence.application.evidence_capture import EvidenceCapture
from jalada.modules.telegram.adapters.telegram_bot import TelegramBot
from jalada.modules.telegram.application.ports import ChatAssistant
from jalada.modules.telegram.application.telegram_capture import TelegramCapture
from jalada.modules.telegram.application.telegram_linking import TelegramLinking
from jalada.modules.telegram.application.telegram_notifier import TelegramNotifier
from jalada.unit_of_work import UnitOfWork


def build_telegram_bot(token: str | None, username: str | None) -> TelegramBot | None:
    """The bot, when both its token and its username are set."""
    if not (token and username):
        return None
    return TelegramBot(token)


def build_telegram_linking(unit_of_work: Callable[[], UnitOfWork], clock: Clock) -> TelegramLinking:
    return TelegramLinking(unit_of_work, clock)


def build_telegram_capture(
    bot: TelegramBot | None,
    linking: TelegramLinking,
    evidence: EvidenceCapture,
    link_limiter: Limiter,
    upload_limiter: Limiter,
    assistant: ChatAssistant | None = None,
) -> TelegramCapture | None:
    if bot is None:
        return None
    return TelegramCapture(linking, evidence, bot, link_limiter, upload_limiter, assistant)


def build_telegram_notifier(
    unit_of_work: Callable[[], UnitOfWork], bot: TelegramBot | None, review_url: str
) -> TelegramNotifier | None:
    if bot is None:
        return None
    return TelegramNotifier(unit_of_work, bot, review_url)
