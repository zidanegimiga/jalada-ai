from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from jalada.modules.pipeline.domain.model import ModelUsage


class Outcome(StrEnum):
    ANSWERED = "answered"
    # A question the assistant never answers, such as tax owed. No model was asked.
    REFUSED = "refused"
    # The answer had figures no tool gave, so it was not sent.
    WITHHELD = "withheld"
    OUT_OF_BUDGET = "out_of_budget"
    # No model could answer.
    FAILED = "failed"


class StepKind(StrEnum):
    MODEL = "model"
    TOOL = "tool"


@dataclass(frozen=True)
class AgentStep:
    """One model call or one tool call. Never the content: names, outcome, cost and time."""

    kind: StepKind
    # The model that answered, or the tool that ran.
    name: str
    # For a model: tool, answer, unusable or failed. For a tool: ok or failed.
    outcome: str
    duration_ms: int
    usage: ModelUsage = ModelUsage()


@dataclass(frozen=True)
class Budget:
    """How much one turn may spend before it stops."""

    max_steps: int = 6
    max_tokens: int = 16000
    max_cost_usd: Decimal = Decimal("0.01")

    def allows(self, model_calls: int, used: ModelUsage) -> bool:
        return (
            model_calls < self.max_steps
            and used.tokens < self.max_tokens
            and used.cost_usd < self.max_cost_usd
        )


@dataclass(frozen=True)
class TurnResult:
    """What a turn produced: the text to show and how it got there."""

    text: str
    outcome: Outcome
    steps: tuple[AgentStep, ...]

    @property
    def usage(self) -> ModelUsage:
        total = ModelUsage()
        for step in self.steps:
            total = total + step.usage
        return total
