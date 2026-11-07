from datetime import UTC, datetime
from types import TracebackType
from typing import Self
from uuid import UUID

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session as DbSession
from sqlalchemy.orm import sessionmaker

from jalada.core.jobs.ports import JobQueue
from jalada.core.jobs.queue import SqlJobQueue
from jalada.modules.accounts.adapters.repositories import SqlSessionRepository, SqlUserRepository
from jalada.modules.accounts.application.ports import SessionRepository, UserRepository
from jalada.modules.evidence.adapters.repository import SqlEvidenceRepository
from jalada.modules.evidence.application.ports import EvidenceRepository
from jalada.modules.ledger.adapters.certificate_payments import SqlCertificatePayments
from jalada.modules.ledger.adapters.ledger_repository import SqlEntryRepository
from jalada.modules.ledger.adapters.preference_repository import SqlPreferenceRepository
from jalada.modules.ledger.application.ports import (
    CertificatePaymentRepository,
    EntryRepository,
    PreferenceRepository,
)
from jalada.modules.pipeline.adapters.run_repository import SqlRunRepository
from jalada.modules.pipeline.application.ports import RunRepository
from jalada.modules.telegram.adapters.telegram_links import SqlTelegramLinks
from jalada.modules.telegram.application.ports import TelegramLinks


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
        self.jobs: JobQueue = SqlJobQueue(self._db, lambda: datetime.now(UTC))
        self.runs: RunRepository = SqlRunRepository(self._db)
        self.telegram: TelegramLinks = SqlTelegramLinks(self._db)
        return self

    def evidence_for(self, user_id: UUID) -> EvidenceRepository:
        return SqlEvidenceRepository(self._db, user_id)

    def entries_for(self, user_id: UUID) -> EntryRepository:
        return SqlEntryRepository(self._db, user_id)

    def preferences_for(self, user_id: UUID) -> PreferenceRepository:
        return SqlPreferenceRepository(self._db, user_id)

    def certificate_payments_for(self, user_id: UUID) -> CertificatePaymentRepository:
        return SqlCertificatePayments(self._db, user_id)

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
