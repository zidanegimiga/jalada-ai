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
