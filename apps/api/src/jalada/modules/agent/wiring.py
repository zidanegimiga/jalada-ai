"""Builds the assistant from the pieces the composition root shares."""

from collections.abc import Callable, Iterable
from typing import Any

from jalada.core.ports import Clock
from jalada.modules.agent.adapters.orchestration.checkpoints import postgres_checkpoints
from jalada.modules.agent.adapters.orchestration.graph import LangGraphRunner
from jalada.modules.agent.application.conversations import Conversations
from jalada.modules.agent.application.tools import Tool, ToolRegistry
from jalada.modules.agent.domain.run import Budget
from jalada.modules.pipeline.domain.model import LanguageModel
from jalada.unit_of_work import UnitOfWork


def build_conversations(
    unit_of_work: Callable[[], UnitOfWork],
    clock: Clock,
    model: LanguageModel | None,
    budget: Budget,
    database_url: str,
    tools: Iterable[Tool[Any]] = (),
) -> Conversations | None:
    """The assistant, when it has a model to run on."""
    if model is None:
        return None
    runner = LangGraphRunner(model, ToolRegistry(tools), budget, postgres_checkpoints(database_url))
    return Conversations(unit_of_work, runner, clock)
