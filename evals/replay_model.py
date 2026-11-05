from decimal import Decimal
from typing import Any

from jalada.pipeline.model import ImageInput, ModelReply, ModelUsage


class ReplayModel:
    """Gives back the model replies stored in a fixture, in order, so evals need no provider."""

    name = "replay"

    def __init__(self, replies: list[dict[str, Any]]) -> None:
        self._replies = list(replies)

    def complete(
        self,
        instructions: str,
        content: str,
        schema: dict[str, Any],
        image: ImageInput | None = None,
    ) -> ModelReply:
        return ModelReply(self._replies.pop(0), ModelUsage(500, 100, Decimal(0)))
