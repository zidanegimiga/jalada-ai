from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DbSession

from jalada.modules.accounts.adapters.tables import SessionRow, UserRow
from jalada.modules.accounts.application.ports import UserCredentials
from jalada.modules.accounts.domain.sessions import Session
from jalada.modules.accounts.domain.users import User
from jalada.shared.errors import EmailAlreadyRegistered


def _to_user(row: UserRow) -> User:
    return User(row.id, row.email, row.display_name, row.created_at)


def _to_credentials(row: UserRow) -> UserCredentials:
    return UserCredentials(_to_user(row), row.password_hash, row.email_verified_at is not None)


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
                # Google only gives verified emails, so an account made through it starts verified.
                email_verified_at=user.created_at if google_subject else None,
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
        return _to_credentials(row) if row else None

    def get_by_google_subject(self, subject: str) -> User | None:
        query = select(UserRow).where(UserRow.google_subject == subject)
        row = self._db.scalars(query).one_or_none()
        return _to_user(row) if row else None

    def delete(self, user_id: UUID) -> None:
        """Removes the user. The database cascades to everything that belongs to them."""
        self._db.execute(delete(UserRow).where(UserRow.id == user_id))

    def link_google(self, user_id: UUID, subject: str, verified_at: datetime) -> None:
        self._db.execute(
            update(UserRow)
            .where(UserRow.id == user_id)
            .values(google_subject=subject, email_verified_at=verified_at)
        )

    def remove_password(self, user_id: UUID) -> None:
        self._db.execute(update(UserRow).where(UserRow.id == user_id).values(password_hash=None))


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

    def delete_all_for(self, user_id: UUID) -> None:
        self._db.execute(delete(SessionRow).where(SessionRow.user_id == user_id))
