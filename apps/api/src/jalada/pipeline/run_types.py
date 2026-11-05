from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from jalada.domain.evidence import EvidenceKind
from jalada.domain.extraction import Classification, Extraction
from jalada.pipeline.model import ImageInput, ModelUsage
from jalada.pipeline.verifier import Verdict


@dataclass(frozen=True)
class Budget:
    max_attempts: int = 3
    max_tokens: int = 8000
    max_cost_usd: Decimal = Decimal("0.02")

    def allows(self, used: ModelUsage) -> bool:
        return used.tokens < self.max_tokens and used.cost_usd < self.max_cost_usd


@dataclass(frozen=True)
class StepRecord:
    step: str
    attempt: int
    input: dict[str, Any]
    output: dict[str, Any]
    verdict: str
    duration_ms: int


@dataclass
class PipelineResult:
    kind: EvidenceKind = EvidenceKind.UNKNOWN
    extraction: Extraction | None = None
    classification: Classification | None = None
    verdict: Verdict | None = None
    # proposed, needs_review or duplicate
    outcome: str = "needs_review"
    attempts: int = 0
    usage: ModelUsage = field(default_factory=ModelUsage)
    steps: list[StepRecord] = field(default_factory=list)


@dataclass(frozen=True)
class EvidenceInput:
    """What the pipeline is given about one piece of evidence."""

    text: str | None
    content_type: str
    image: ImageInput | None = None
