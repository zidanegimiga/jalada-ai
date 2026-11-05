"""Fake repositories for users and sessions."""

from datetime import datetime
from uuid import UUID

from jalada.application.ports import (
    UserCredentials,
)
from jalada.domain.sessions import Session
from jalada.domain.users import User


class FakeUsers:
    def __init__(
        self, users: dict[UUID, UserCredentials], google_subjects: dict[str, UUID]
    ) -> None:
        self.rows = users
        self.google_subjects = google_subjects

    def add(self, user: User, password_hash: str | None, google_subject: str | None = None) -> None:
        self.rows[user.id] = UserCredentials(user, password_hash)
        if google_subject:
            self.google_subjects[google_subject] = user.id

    def get(self, user_id: UUID) -> User | None:
        found = self.rows.get(user_id)
        return found.user if found else None

    def get_credentials(self, email: str) -> UserCredentials | None:
        return next((c for c in self.rows.values() if c.user.email == email), None)

    def get_by_google_subject(self, subject: str) -> User | None:
        user_id = self.google_subjects.get(subject)
        return self.get(user_id) if user_id else None

    def link_google(self, user_id: UUID, subject: str) -> None:
        self.google_subjects[subject] = user_id


class FakeSessions:
    def __init__(self, sessions: dict[str, Session]) -> None:
        self.rows = sessions

    def add(self, session: Session) -> None:
        self.rows[session.token_hash] = session

    def get_active(self, token_hash: str, now: datetime) -> Session | None:
        session = self.rows.get(token_hash)
        return session if session and session.expires_at > now else None

    def delete(self, token_hash: str) -> None:
        self.rows.pop(token_hash, None)


class FakeTelegramLinks:
    def __init__(
        self,
        codes: dict[str, tuple[UUID, datetime]],
        links: dict[UUID, tuple[int, int]],
    ) -> None:
        self.codes = codes
        # user id to (Telegram user id, chat id)
        self.links = links

    def save_code(self, user_id: UUID, code_hash: str, expires_at: datetime) -> None:
        for old in [h for h, (owner, _) in self.codes.items() if owner == user_id]:
            del self.codes[old]
        self.codes[code_hash] = (user_id, expires_at)

    def use_code(self, code_hash: str, now: datetime) -> UUID | None:
        found = self.codes.pop(code_hash, None)
        return found[0] if found and found[1] > now else None

    def link(self, user_id: UUID, telegram_user_id: int, chat_id: int, at: datetime) -> None:
        for other in [u for u, (t, _) in self.links.items() if t == telegram_user_id]:
            del self.links[other]
        self.links[user_id] = (telegram_user_id, chat_id)

    def user_for(self, telegram_user_id: int) -> UUID | None:
        return next((u for u, (t, _) in self.links.items() if t == telegram_user_id), None)

    def chat_for(self, user_id: UUID) -> int | None:
        found = self.links.get(user_id)
        return found[1] if found else None
