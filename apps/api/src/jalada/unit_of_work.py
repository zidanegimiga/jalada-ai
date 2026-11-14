from types import TracebackType
from typing import Protocol, Self
from uuid import UUID

from jalada.core.jobs.ports import JobQueue
from jalada.modules.accounts.application.ports import SessionRepository, UserRepository
from jalada.modules.evidence.application.ports import EvidenceRepository
from jalada.modules.ledger.application.ports import (
    CertificatePaymentRepository,
    EntryRepository,
    MoneyAccountRepository,
    PreferenceRepository,
    TransactionRepository,
)
from jalada.modules.pipeline.application.ports import RunRepository
from jalada.modules.telegram.application.ports import TelegramLinks


class UnitOfWork(Protocol):
    """One database transaction. Nothing is saved unless `commit` is called."""

    users: UserRepository
    sessions: SessionRepository
    jobs: JobQueue
    runs: RunRepository
    telegram: TelegramLinks

    def evidence_for(self, user_id: UUID) -> EvidenceRepository: ...
    def entries_for(self, user_id: UUID) -> EntryRepository: ...
    def preferences_for(self, user_id: UUID) -> PreferenceRepository: ...
    def certificate_payments_for(self, user_id: UUID) -> CertificatePaymentRepository: ...
    def money_accounts_for(self, user_id: UUID) -> MoneyAccountRepository: ...
    def transactions_for(self, user_id: UUID) -> TransactionRepository: ...

    def __enter__(self) -> Self: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...
    def commit(self) -> None: ...
