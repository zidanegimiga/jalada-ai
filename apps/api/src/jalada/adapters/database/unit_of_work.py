from types import TracebackType
from typing import Self

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session as DbSession
from sqlalchemy.orm import sessionmaker

from jalada.adapters.database.repositories import SqlSessionRepository, SqlUserRepository
from jalada.application.ports import SessionRepository, UserRepository


def create_database_engine(database_url: str) -> Engine:
    # pool_pre_ping drops connections the database closed, common on free hosted tiers.
    return create_engine(database_url, pool_pre_ping=True)


class SqlUnitOfWork:
    def __init__(self, session_factory: sessionmaker[DbSession]) -> None:
        self._session_factory = session_factory

    def __enter__(self) -> Self:
        self._db = self._session_factory()
        self.users: UserRepository = SqlUserRepository(self._db)
        self.sessions: SessionRepository = SqlSessionRepository(self._db)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._db.rollback()
        self._db.close()

    def commit(self) -> None:
        self._db.commit()
