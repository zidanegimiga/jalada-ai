"""Every table in the database, so Alembic sees them all when it compares models with
migrations. Each module defines its own tables on the shared Base."""

from jalada.core.database.base import Base
from jalada.core.idempotency.tables import IdempotencyKeyRow
from jalada.core.jobs.tables import JobRow
from jalada.modules.accounts.adapters.tables import ModelConsentRow, SessionRow, UserRow
from jalada.modules.agent.adapters.tables import (
    AgentActionRow,
    AgentMessageRow,
    AgentRunRow,
    AgentStepRow,
    AgentThreadRow,
)
from jalada.modules.evidence.adapters.tables import EvidenceRow
from jalada.modules.ledger.adapters.suggestion_tables import MatchSuggestionRow
from jalada.modules.ledger.adapters.tables import (
    AuditEventRow,
    CertificatePaymentRow,
    CounterpartyPreferenceRow,
    EntryRevisionRow,
    EntryRow,
    MoneyAccountRow,
    TransactionEvidenceRow,
    TransactionLineRow,
    TransactionRow,
)
from jalada.modules.pipeline.adapters.tables import PipelineRunRow, PipelineStepRow
from jalada.modules.telegram.adapters.tables import TelegramLinkCodeRow, TelegramLinkRow

ALL_TABLES: list[type[Base]] = [
    UserRow,
    SessionRow,
    ModelConsentRow,
    EvidenceRow,
    JobRow,
    IdempotencyKeyRow,
    PipelineRunRow,
    PipelineStepRow,
    EntryRow,
    EntryRevisionRow,
    CertificatePaymentRow,
    CounterpartyPreferenceRow,
    MoneyAccountRow,
    TransactionRow,
    TransactionLineRow,
    TransactionEvidenceRow,
    AuditEventRow,
    MatchSuggestionRow,
    TelegramLinkRow,
    TelegramLinkCodeRow,
    AgentThreadRow,
    AgentMessageRow,
    AgentRunRow,
    AgentStepRow,
    AgentActionRow,
]
