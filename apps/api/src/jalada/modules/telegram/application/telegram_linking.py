from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from jalada.core.ports import Clock
from jalada.modules.telegram.domain.telegram import CODE_MINUTES, hash_link_code, new_link_code
from jalada.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class LinkCode:
    code: str
    expires_at: datetime


class TelegramLinking:
    """Tying a Telegram account to a user, with a short-lived one-time code."""

    def __init__(self, unit_of_work: Callable[[], UnitOfWork], clock: Clock) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    def new_code(self, user_id: UUID) -> LinkCode:
        code = new_link_code()
        expires_at = self._clock.now() + timedelta(minutes=CODE_MINUTES)
        with self._unit_of_work() as work:
            work.telegram.save_code(user_id, hash_link_code(code), expires_at)
            work.commit()
        return LinkCode(code, expires_at)

    def link(self, code: str, telegram_user_id: int, chat_id: int) -> UUID | None:
        """The linked user, or None when the code is wrong or expired."""
        now = self._clock.now()
        with self._unit_of_work() as work:
            user_id = work.telegram.use_code(hash_link_code(code), now)
            if user_id is not None:
                work.telegram.link(user_id, telegram_user_id, chat_id, now)
            work.commit()
        return user_id

    def is_linked(self, user_id: UUID) -> bool:
        with self._unit_of_work() as work:
            return work.telegram.chat_for(user_id) is not None

    def user_for(self, telegram_user_id: int) -> UUID | None:
        with self._unit_of_work() as work:
            return work.telegram.user_for(telegram_user_id)
