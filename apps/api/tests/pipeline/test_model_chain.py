from decimal import Decimal
from typing import Any

import pytest

from jalada.core.resilience.failures import FailureKind, ProviderFailure
from jalada.core.resilience.retry import RetryPolicy
from jalada.modules.pipeline.adapters.models.chain import ChainLink, ModelChain
from jalada.modules.pipeline.adapters.models.profiles import ModelProfile
from jalada.modules.pipeline.domain.model import ImageInput, ModelFailed, ModelReply, ModelUsage

SCHEMA = {
    "type": "object",
    "properties": {"amount_ksh": {"type": "string"}},
    "required": ["amount_ksh"],
}
PHOTO = ImageInput(b"\xff\xd8", "image/jpeg")


class Model:
    def __init__(self, name: str, *answers: dict[str, Any] | ProviderFailure) -> None:
        self.name = name
        self.answers = list(answers)
        self.calls = 0

    def complete(
        self,
        instructions: str,
        content: str,
        schema: dict[str, Any],
        image: ImageInput | None = None,
    ) -> ModelReply:
        self.calls += 1
        answer = self.answers.pop(0)
        if isinstance(answer, ProviderFailure):
            raise answer
        return ModelReply(answer, ModelUsage(100, 10, Decimal(0)))


def link(model: Model, vision: bool = True, context: int = 100_000) -> ChainLink:
    profile = ModelProfile(
        name=model.name, provider="test", model=model.name, vision=vision, context_tokens=context
    )
    return ChainLink(profile, model)


def chain(*links: ChainLink) -> ModelChain:
    return ModelChain(links, retry=RetryPolicy(tries=2, jitter=lambda: 1.0), sleep=lambda _: None)


def test_a_wrong_answer_moves_on_to_the_next_model_and_is_recorded() -> None:
    primary = Model("primary", {"total": "1.00"})
    backup = Model("backup", {"amount_ksh": "1.00"})

    reply = chain(link(primary), link(backup)).complete("i", "c", SCHEMA)

    assert reply.data == {"amount_ksh": "1.00"}
    assert reply.answered_by == "backup"
    assert [(a["model"], a["outcome"]) for a in reply.attempts] == [
        ("primary", "bad_output"),
        ("backup", "ok"),
    ]


def test_a_rate_limit_is_retried_on_the_same_model() -> None:
    primary = Model("primary", ProviderFailure(FailureKind.RATE_LIMITED), {"amount_ksh": "2.00"})

    reply = chain(link(primary)).complete("i", "c", SCHEMA)

    assert reply.answered_by == "primary" and primary.calls == 2


def test_photos_skip_models_that_cannot_see() -> None:
    blind = Model("blind", {"amount_ksh": "1.00"})
    sighted = Model("sighted", {"amount_ksh": "3.00"})

    reply = chain(link(blind, vision=False), link(sighted)).complete("i", "c", SCHEMA, PHOTO)

    assert reply.answered_by == "sighted" and blind.calls == 0


def test_inputs_too_large_for_a_model_skip_it() -> None:
    small = Model("small", {"amount_ksh": "1.00"})
    large = Model("large", {"amount_ksh": "4.00"})

    reply = chain(link(small, context=1_000), link(large)).complete("i", "x" * 30_000, SCHEMA)

    assert reply.answered_by == "large" and small.calls == 0


def test_when_every_model_fails_the_pipeline_is_told_which_and_why() -> None:
    refused = Model("refuses", ProviderFailure(FailureKind.REFUSED))
    blind = Model("blind")

    with pytest.raises(ModelFailed) as failed:
        chain(link(refused), link(blind, vision=False)).complete("i", "c", SCHEMA, PHOTO)

    assert str(failed.value) == "refuses: refused"


def test_the_chain_names_its_models_in_order() -> None:
    assert chain(link(Model("a")), link(Model("b"))).name == "chain:a,b"
