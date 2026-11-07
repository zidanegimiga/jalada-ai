"""A model that is really an ordered chain of models (chain of responsibility).

Each call goes to the first eligible model. Rate limits, timeouts and outages are retried
with backoff; wrong or unusable answers, inputs too large for the model, refusals and bad
settings move on to the next model. Which models are eligible for a call is a strategy.
"""

import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from typing import Any, Protocol

from jalada.core.resilience.breaker import CircuitBreaker
from jalada.core.resilience.failures import FailureKind, ProviderFailure
from jalada.core.resilience.fallback import AllProvidersFailed, Attempt, FallbackChain
from jalada.core.resilience.retry import RetryPolicy
from jalada.modules.pipeline.adapters.models.output_check import problems
from jalada.modules.pipeline.adapters.models.profiles import ModelProfile
from jalada.modules.pipeline.domain.model import ImageInput, LanguageModel, ModelFailed, ModelReply

# A rough, cautious token count: about three characters a token, plus room for a photo
# and for the answer itself.
CHARACTERS_PER_TOKEN = 3
TOKENS_PER_IMAGE = 2_000
TOKENS_FOR_ANSWER = 2_000


@dataclass(frozen=True)
class Call:
    """What one request needs from a model, for deciding which models can take it."""

    needs_vision: bool
    estimated_tokens: int


@dataclass(frozen=True)
class ChainLink:
    profile: ModelProfile
    model: LanguageModel


class Selection(Protocol):
    """Strategy: may this model take this call?"""

    def allows(self, profile: ModelProfile, call: Call) -> bool: ...


class ByCapability:
    """The default strategy: photos only go to models that can see, and nothing goes to a
    model whose context window is too small for it."""

    def allows(self, profile: ModelProfile, call: Call) -> bool:
        if call.needs_vision and not profile.vision:
            return False
        return call.estimated_tokens <= profile.context_tokens


class ModelChain:
    """Implements LanguageModel, so the pipeline neither knows nor cares how many models
    there are or which one answered."""

    def __init__(
        self,
        links: Sequence[ChainLink],
        retry: RetryPolicy | None = None,
        breaker: CircuitBreaker | None = None,
        selection: Selection | None = None,
        sleep: Callable[[float], None] | None = None,
    ) -> None:
        self.links = list(links)
        self.name = "chain:" + ",".join(link.profile.name for link in self.links)
        self._selection = selection or ByCapability()
        self._chain: FallbackChain[ChainLink] = FallbackChain(
            self.links,
            lambda link: link.profile.name,
            retry or RetryPolicy(),
            breaker or CircuitBreaker(),
            sleep=sleep or time.sleep,
        )

    def complete(
        self,
        instructions: str,
        content: str,
        schema: dict[str, Any],
        image: ImageInput | None = None,
    ) -> ModelReply:
        call = Call(image is not None, _estimate(instructions, content, image))

        def ask(link: ChainLink) -> ModelReply:
            reply = link.model.complete(instructions, content, schema, image)
            if problems(reply.data, schema):
                raise ProviderFailure(FailureKind.BAD_OUTPUT)
            return reply

        try:
            reply, used, attempts = self._chain.run(
                ask, lambda link: self._selection.allows(link.profile, call)
            )
        except AllProvidersFailed as failed:
            raise ModelFailed(_summary(failed.attempts)) from failed
        return replace(reply, answered_by=used.profile.name, attempts=_records(attempts))


def _estimate(instructions: str, content: str, image: ImageInput | None) -> int:
    text = (len(instructions) + len(content)) // CHARACTERS_PER_TOKEN
    return text + (TOKENS_PER_IMAGE if image else 0) + TOKENS_FOR_ANSWER


def _records(attempts: list[Attempt]) -> tuple[dict[str, Any], ...]:
    return tuple(
        {"model": a.provider, "outcome": a.outcome, "latency_ms": a.latency_ms} for a in attempts
    )


def _summary(attempts: list[Attempt]) -> str:
    if not attempts:
        return "no model could take this request"
    return "; ".join(f"{a.provider}: {a.outcome}" for a in attempts)
