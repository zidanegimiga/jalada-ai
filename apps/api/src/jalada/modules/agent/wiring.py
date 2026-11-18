"""Builds the assistant from the pieces the composition root shares."""

import json
from collections.abc import Callable, Iterable, Mapping
from typing import Any
from uuid import UUID

from jalada.core.ports import Clock
from jalada.modules.agent.adapters.orchestration.checkpoints import postgres_checkpoints
from jalada.modules.agent.adapters.orchestration.graph import LangGraphRunner
from jalada.modules.agent.adapters.telemetry import otlp_tracer
from jalada.modules.agent.application.confirmations import ActionConfirmations, Executor
from jalada.modules.agent.application.conversations import Conversations
from jalada.modules.agent.application.lookups.exports import TaxYearWorkbook
from jalada.modules.agent.application.lookups.payments import AddUpPayments, SearchPayments
from jalada.modules.agent.application.lookups.review import PaymentDetails, WaitingToCheck
from jalada.modules.agent.application.lookups.summaries import MonthlySummary, SpendingByCategory
from jalada.modules.agent.application.ports import NoTracing, TurnTracer
from jalada.modules.agent.application.proposals import ActionProposals
from jalada.modules.agent.application.suggestions import SuggestCategory, SuggestConfirm
from jalada.modules.agent.application.tools import Tool, ToolRegistry
from jalada.modules.agent.domain.proposals import ActionKind
from jalada.modules.agent.domain.run import Budget
from jalada.modules.ledger.application.entry_review import EntryReview
from jalada.modules.ledger.application.ledger import Ledger
from jalada.modules.ledger.domain.entries import Correction
from jalada.modules.pipeline.domain.model import LanguageModel
from jalada.unit_of_work import UnitOfWork


def build_lookups(
    ledger: Ledger,
    review: EntryReview,
    public_url: str,
    proposals: ActionProposals | None = None,
) -> list[Tool[Any]]:
    """Every tool the assistant has. They only read, or keep a suggestion for the person."""
    lookups: list[Tool[Any]] = [
        SearchPayments(ledger),
        AddUpPayments(ledger),
        SpendingByCategory(ledger),
        MonthlySummary(ledger),
        WaitingToCheck(review),
        PaymentDetails(ledger),
        TaxYearWorkbook(public_url),
    ]
    if proposals is not None:
        lookups += [SuggestConfirm(review, proposals), SuggestCategory(ledger, proposals)]
    return lookups


def build_conversations(
    unit_of_work: Callable[[], UnitOfWork],
    clock: Clock,
    model: LanguageModel | None,
    budget: Budget,
    database_url: str,
    tools: Iterable[Tool[Any]] = (),
    tracer: TurnTracer | None = None,
    deep_model: LanguageModel | None = None,
    may_ask: Callable[[UUID], bool] = lambda _: True,
) -> Conversations | None:
    """The assistant, when it has a model to run on. `model` answers single lookups and
    `deep_model`, when given, the harder questions."""
    if model is None:
        return None
    runner = LangGraphRunner(
        model, ToolRegistry(tools), budget, postgres_checkpoints(database_url), deep_model
    )
    return Conversations(unit_of_work, runner, clock, tracer=tracer, may_ask=may_ask)


def build_confirmations(
    unit_of_work: Callable[[], UnitOfWork], clock: Clock, review: EntryReview
) -> ActionConfirmations:
    """Each kind of suggested change, made through the ledger's own use case."""

    def confirm_payment(user_id: UUID, payload: Mapping[str, str]) -> None:
        review.confirm(user_id, UUID(payload["entry_id"]))

    def change_category(user_id: UUID, payload: Mapping[str, str]) -> None:
        review.confirm(user_id, UUID(payload["entry_id"]), Correction(category=payload["category"]))

    executors: dict[ActionKind, Executor] = {
        ActionKind.CONFIRM_PAYMENT: confirm_payment,
        ActionKind.CHANGE_CATEGORY: change_category,
    }
    return ActionConfirmations(unit_of_work, clock, executors)


def build_tracer(url: str | None, headers_json: str | None, version: str) -> TurnTracer:
    """Traces go to the OTLP address when one is set, and nowhere otherwise."""
    if not url:
        return NoTracing()
    headers = json.loads(headers_json) if headers_json else {}
    if not isinstance(headers, dict):
        raise ValueError("JALADA_AGENT_TRACES_HEADERS must be a JSON object")
    return otlp_tracer(url, {str(k): str(v) for k, v in headers.items()}, version)
