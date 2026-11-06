from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from jalada.modules.evidence.domain.evidence import Evidence
from jalada.modules.ledger.domain.entries import Entry
from jalada.modules.pipeline.domain.run_types import StepRecord


@dataclass(frozen=True)
class PipelineRun:
    id: UUID
    user_id: UUID
    evidence_id: UUID
    outcome: str
    attempts: int
    input_tokens: int
    output_tokens: int
    cost_usd: Decimal
    started_at: datetime
    finished_at: datetime


class RunRepository(Protocol):
    def add(self, run: PipelineRun, steps: list[StepRecord]) -> None: ...
    def for_user(self, user_id: UUID) -> list[tuple[PipelineRun, list[StepRecord]]]: ...


class TextReader(Protocol):
    """Turns stored evidence into text. None when there is no text to read."""

    def read(self, content_type: str, data: bytes) -> str | None: ...


class ProcessingNotifier(Protocol):
    """Tells the user what the pipeline made of their evidence."""

    def notify(
        self, evidence: Evidence, outcome: str, entry: Entry | None, reasons: list[str]
    ) -> None:
        """`reasons` are the verifier's reasons for holding the entry back, if any."""
        ...
