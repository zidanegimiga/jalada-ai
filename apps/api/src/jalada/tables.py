"""Every table in the database, so Alembic sees them all when it compares models with
migrations. Each module defines its own tables on the shared Base."""

from jalada.core.database.base import Base
from jalada.core.jobs.tables import JobRow
from jalada.modules.accounts.adapters.tables import SessionRow, UserRow
from jalada.modules.evidence.adapters.tables import EvidenceRow
from jalada.modules.ledger.adapters.tables import (
    CertificatePaymentRow,
    CounterpartyPreferenceRow,
    EntryRevisionRow,
    EntryRow,
)
from jalada.modules.pipeline.adapters.tables import PipelineRunRow, PipelineStepRow
from jalada.modules.telegram.adapters.tables import TelegramLinkCodeRow, TelegramLinkRow

ALL_TABLES: list[type[Base]] = [
    UserRow,
    SessionRow,
    EvidenceRow,
    JobRow,
    PipelineRunRow,
    PipelineStepRow,
    EntryRow,
    EntryRevisionRow,
    CertificatePaymentRow,
    CounterpartyPreferenceRow,
    TelegramLinkRow,
    TelegramLinkCodeRow,
]
