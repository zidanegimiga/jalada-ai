from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DbSession

from jalada.adapters.database.tables import SessionRow, UserRow
from jalada.application.errors import EmailAlreadyRegistered
from jalada.application.ports import UserCredentials
from jalada.domain.sessions import Session
from jalada.domain.users import User


def _to_user(row: UserRow) -> User:
    return User(row.id, row.email, row.display_name, row.created_at)


class SqlUserRepository:
    def __init__(self, db: DbSession) -> None:
        self._db = db

    def add(self, user: User, password_hash: str | None, google_subject: str | None = None) -> None:
        self._db.add(
            UserRow(
                id=user.id,
                email=user.email,
                password_hash=password_hash,
                google_subject=google_subject,
                display_name=user.display_name,
                created_at=user.created_at,
            )
        )
        try:
            self._db.flush()
        except IntegrityError as error:
            # Two sign-ups with the same email at the same moment: the unique index decides.
            raise EmailAlreadyRegistered from error

    def get(self, user_id: UUID) -> User | None:
        row = self._db.get(UserRow, user_id)
        return _to_user(row) if row else None

    def get_credentials(self, email: str) -> UserCredentials | None:
        row = self._db.scalars(select(UserRow).where(UserRow.email == email)).one_or_none()
        return UserCredentials(_to_user(row), row.password_hash) if row else None

    def get_by_google_subject(self, subject: str) -> User | None:
        query = select(UserRow).where(UserRow.google_subject == subject)
        row = self._db.scalars(query).one_or_none()
        return _to_user(row) if row else None

    def link_google(self, user_id: UUID, subject: str) -> None:
        self._db.execute(
            update(UserRow).where(UserRow.id == user_id).values(google_subject=subject)
        )


class SqlSessionRepository:
    def __init__(self, db: DbSession) -> None:
        self._db = db

    def add(self, session: Session) -> None:
        self._db.add(
            SessionRow(
                token_hash=session.token_hash,
                user_id=session.user_id,
                expires_at=session.expires_at,
            )
        )

    def get_active(self, token_hash: str, now: datetime) -> Session | None:
        row = self._db.scalars(
            select(SessionRow).where(
                SessionRow.token_hash == token_hash, SessionRow.expires_at > now
            )
        ).one_or_none()
        return Session(row.token_hash, row.user_id, row.expires_at) if row else None

    def delete(self, token_hash: str) -> None:
        self._db.execute(delete(SessionRow).where(SessionRow.token_hash == token_hash))
