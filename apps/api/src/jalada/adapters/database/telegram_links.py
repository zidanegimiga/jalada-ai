from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session as DbSession

from jalada.adapters.database.tables import TelegramLinkCodeRow, TelegramLinkRow


class SqlTelegramLinks:
    def __init__(self, db: DbSession) -> None:
        self._db = db

    def save_code(self, user_id: UUID, code_hash: str, expires_at: datetime) -> None:
        """A new code replaces any earlier one, so only the latest works."""
        self._db.execute(delete(TelegramLinkCodeRow).where(TelegramLinkCodeRow.user_id == user_id))
        self._db.add(
            TelegramLinkCodeRow(code_hash=code_hash, user_id=user_id, expires_at=expires_at)
        )

    def use_code(self, code_hash: str, now: datetime) -> UUID | None:
        """The code's owner, if it is still valid. Either way the code is used up."""
        row = self._db.get(TelegramLinkCodeRow, code_hash)
        if row is None:
            return None
        self._db.delete(row)
        return row.user_id if row.expires_at > now else None

    def link(self, user_id: UUID, telegram_user_id: int, chat_id: int, at: datetime) -> None:
        # Linking again moves the link: one Telegram account per user, one user per account.
        self._db.execute(
            delete(TelegramLinkRow).where(
                (TelegramLinkRow.user_id == user_id)
                | (TelegramLinkRow.telegram_user_id == telegram_user_id)
            )
        )
        self._db.add(
            TelegramLinkRow(
                user_id=user_id, telegram_user_id=telegram_user_id, chat_id=chat_id, linked_at=at
            )
        )

    def user_for(self, telegram_user_id: int) -> UUID | None:
        query = select(TelegramLinkRow.user_id).where(
            TelegramLinkRow.telegram_user_id == telegram_user_id
        )
        return self._db.scalar(query)

    def chat_for(self, user_id: UUID) -> int | None:
        return self._db.scalar(
            select(TelegramLinkRow.chat_id).where(TelegramLinkRow.user_id == user_id)
        )
