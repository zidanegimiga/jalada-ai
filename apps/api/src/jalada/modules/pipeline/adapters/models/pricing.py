from dataclasses import dataclass
from decimal import Decimal

from jalada.modules.pipeline.domain.model import ModelUsage

MILLION = Decimal(1_000_000)


@dataclass(frozen=True)
class Pricing:
    """US dollars per million tokens. Zero for free tiers and local models."""

    input_per_million: Decimal = Decimal(0)
    output_per_million: Decimal = Decimal(0)

    def usage(self, input_tokens: int, output_tokens: int) -> ModelUsage:
        cost = (
            input_tokens * self.input_per_million + output_tokens * self.output_per_million
        ) / MILLION
        return ModelUsage(input_tokens, output_tokens, cost)
