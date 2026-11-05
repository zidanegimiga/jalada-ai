from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Protocol


@dataclass(frozen=True)
class ImageInput:
    data: bytes
    content_type: str


@dataclass(frozen=True)
class ModelUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: Decimal = Decimal(0)

    def __add__(self, other: "ModelUsage") -> "ModelUsage":
        return ModelUsage(
            self.input_tokens + other.input_tokens,
            self.output_tokens + other.output_tokens,
            self.cost_usd + other.cost_usd,
        )

    @property
    def tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass(frozen=True)
class ModelReply:
    """JSON from the model, not yet trusted, and what the call cost."""

    data: dict[str, Any]
    usage: ModelUsage


class ModelFailed(Exception):
    """The provider could not be reached or returned something that is not JSON."""


class LanguageModel(Protocol):
    """Any provider that can answer in JSON matching a schema, given text or a photo."""

    name: str

    def complete(
        self,
        instructions: str,
        content: str,
        schema: dict[str, Any],
        image: ImageInput | None = None,
    ) -> ModelReply: ...
