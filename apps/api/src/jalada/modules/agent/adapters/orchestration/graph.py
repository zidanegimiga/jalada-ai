"""One turn as a graph: screen, decide, look up, decide again, then check the answer.

    screen -> decide -> act -> decide -> ... -> check -> done
       \\-> done (a refused question)            \\-> decide (once, if an amount was not
                                                       in the records)

The person's id and question travel in the run's context, which is never put in a prompt.
The state holds only what the turn has done so far, as plain data, so it can be checkpointed.
"""

import logging
from decimal import Decimal
from time import perf_counter
from typing import Any, TypedDict

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.runtime import Runtime

from jalada.modules.agent.application.next_step import NEXT_STEP_SCHEMA, Unusable, read_decision
from jalada.modules.agent.application.ports import TurnRequest
from jalada.modules.agent.application.prompts import instructions, records, turn_content
from jalada.modules.agent.application.tools import ToolContext, ToolRegistry
from jalada.modules.agent.domain.actions import ToolCall
from jalada.modules.agent.domain.grounding import ungrounded
from jalada.modules.agent.domain.policy import refusal_for
from jalada.modules.agent.domain.progress import OnProgress, Progress, Stage, ignore
from jalada.modules.agent.domain.run import AgentStep, Budget, Outcome, StepKind, TurnResult
from jalada.modules.pipeline.domain.model import LanguageModel, ModelFailed, ModelUsage

logger = logging.getLogger(__name__)

OUT_OF_BUDGET = (
    "That needed more looking up than I can do in one go. Try asking about one thing at a time."
)
FAILED = "I cannot answer right now. Please try again in a little while."
WITHHELD = (
    "I could not match the figures in my answer to your records, so I have not given it. "
    "Try asking in a different way."
)
LOOKUP_FAILED = {"error": "This lookup failed. Answer without it or say it is not available."}


class TurnState(TypedDict, total=False):
    work: list[dict[str, Any]]
    steps: list[dict[str, Any]]
    model_calls: int
    pending: dict[str, Any] | None
    draft: str | None
    rechecked: bool
    text: str
    outcome: str


class LangGraphRunner:
    def __init__(
        self,
        model: LanguageModel,
        tools: ToolRegistry,
        budget: Budget,
        checkpointer: BaseCheckpointSaver[str] | None = None,
    ) -> None:
        self._model = model
        self._tools = tools
        self._budget = budget
        self._checkpointer = checkpointer
        self._instructions = instructions(tools)
        self._graph = self._build().compile(checkpointer=checkpointer)

    def run(self, request: TurnRequest, on_progress: OnProgress = ignore) -> TurnResult:
        thread = str(request.run_id)
        config: Any = {
            "configurable": {"thread_id": thread},
            "recursion_limit": self._budget.max_steps * 3 + 5,
        }
        start: TurnState = {"work": [], "steps": [], "model_calls": 0, "rechecked": False}
        final: dict[str, Any] = {}
        # Nodes report progress on the custom stream; the values stream ends with the result.
        for mode, chunk in self._graph.stream(
            start, config, context=request, stream_mode=["custom", "values"]
        ):
            if mode == "custom" and isinstance(chunk, Progress):
                on_progress(chunk)
            elif mode == "values" and isinstance(chunk, dict):
                final = chunk
        if self._checkpointer is not None:
            # A finished turn needs no checkpoint; one paused for a person would keep it.
            self._checkpointer.delete_thread(thread)
        steps = tuple(_step(s) for s in final["steps"])
        return TurnResult(final["text"], Outcome(final["outcome"]), steps)

    def _build(self) -> StateGraph[TurnState, TurnRequest, TurnState, TurnState]:
        graph = StateGraph(TurnState, context_schema=TurnRequest)
        graph.add_node("screen", _screen)
        graph.add_node("decide", self._decide)
        graph.add_node("act", self._act)
        graph.add_node("check", self._check)
        graph.add_edge(START, "screen")
        graph.add_conditional_edges("screen", _after_check, ["decide", END])
        graph.add_conditional_edges("decide", _after_decide, ["decide", "act", "check", END])
        graph.add_edge("act", "decide")
        graph.add_conditional_edges("check", _after_check, ["decide", END])
        return graph

    def _decide(self, state: TurnState, runtime: Runtime[TurnRequest]) -> TurnState:
        turn = runtime.context
        steps, work, calls = state["steps"], state["work"], state["model_calls"]
        if not self._budget.allows(calls, _usage(steps)):
            return {"outcome": Outcome.OUT_OF_BUDGET, "text": OUT_OF_BUDGET}
        content = turn_content(turn.question, turn.history, work, turn.today)
        runtime.stream_writer(Progress(Stage.THINKING))
        started = perf_counter()
        try:
            reply = self._model.complete(self._instructions, content, NEXT_STEP_SCHEMA)
        except ModelFailed:
            step = _model_step(self._model.name, "failed", started, ModelUsage())
            return {"steps": [*steps, step], "outcome": Outcome.FAILED, "text": FAILED}
        answered_by = reply.answered_by or self._model.name
        try:
            decision = read_decision(reply.data, self._tools)
        except Unusable as problem:
            step = _model_step(answered_by, "unusable", started, reply.usage)
            note = {"note": f"Your last reply could not be used: {problem}"}
            return {
                "steps": [*steps, step],
                "model_calls": calls + 1,
                "work": [*work, note],
                "pending": None,
                "draft": None,
            }
        if isinstance(decision, ToolCall):
            step = _model_step(answered_by, "tool", started, reply.usage)
            pending = {"tool": decision.tool, "arguments": decision.arguments}
            return {"steps": [*steps, step], "model_calls": calls + 1, "pending": pending}
        step = _model_step(answered_by, "answer", started, reply.usage)
        return {"steps": [*steps, step], "model_calls": calls + 1, "draft": decision.text}

    def _act(self, state: TurnState, runtime: Runtime[TurnRequest]) -> TurnState:
        call = state.get("pending") or {}
        tool = self._tools.get(call.get("tool", ""))
        turn = runtime.context
        context = ToolContext(turn.user_id, turn.today, turn.run_id, turn.thread_id)
        if tool is not None:
            runtime.stream_writer(Progress(Stage.LOOKING_UP, tool.name, tool.label))
        started = perf_counter()
        outcome = "ok"
        try:
            if tool is None:
                raise LookupError(call.get("tool"))
            result = tool.call(context, call.get("arguments", {}))
        except Exception:
            # Logged without the message, which can repeat the person's records.
            logger.error("Assistant tool failed", extra={"tool": call.get("tool")})
            result, outcome = LOOKUP_FAILED, "failed"
        step = {
            "kind": StepKind.TOOL,
            "name": str(call.get("tool", "")),
            "outcome": outcome,
            "duration_ms": _ms_since(started),
        }
        item = {"tool": call.get("tool"), "arguments": call.get("arguments", {}), "result": result}
        return {
            "steps": [*state["steps"], step],
            "work": [*state["work"], item],
            "pending": None,
        }

    def _check(self, state: TurnState, runtime: Runtime[TurnRequest]) -> TurnState:
        draft = state.get("draft") or ""
        runtime.stream_writer(Progress(Stage.CHECKING))
        sources = [records(item["result"]) for item in state["work"] if "result" in item]
        missing = ungrounded(draft, [runtime.context.question, *sources])
        if not missing:
            return {"outcome": Outcome.ANSWERED, "text": draft}
        if state["rechecked"]:
            return {"outcome": Outcome.WITHHELD, "text": WITHHELD}
        listed = ", ".join(format(amount, "f") for amount in missing)
        note = {
            "note": f"Your answer had amounts no tool returned: {listed}. Use only amounts "
            "from the records, look them up, or say you could not find them."
        }
        return {"work": [*state["work"], note], "rechecked": True, "draft": None}


def _screen(state: TurnState, runtime: Runtime[TurnRequest]) -> TurnState:
    refusal = refusal_for(runtime.context.question)
    return {"outcome": Outcome.REFUSED, "text": refusal} if refusal else {}


def _after_decide(state: TurnState) -> str:
    if state.get("outcome"):
        return END
    if state.get("pending"):
        return "act"
    if state.get("draft"):
        return "check"
    return "decide"


def _after_check(state: TurnState) -> str:
    return END if state.get("outcome") else "decide"


def _model_step(name: str, outcome: str, started: float, usage: ModelUsage) -> dict[str, Any]:
    return {
        "kind": StepKind.MODEL,
        "name": name,
        "outcome": outcome,
        "duration_ms": _ms_since(started),
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "cost_usd": str(usage.cost_usd),
    }


def _step(data: dict[str, Any]) -> AgentStep:
    usage = ModelUsage(
        data.get("input_tokens", 0), data.get("output_tokens", 0), Decimal(data.get("cost_usd", 0))
    )
    return AgentStep(
        StepKind(data["kind"]), data["name"], data["outcome"], data["duration_ms"], usage
    )


def _usage(steps: list[dict[str, Any]]) -> ModelUsage:
    return sum((_step(s).usage for s in steps), ModelUsage())


def _ms_since(started: float) -> int:
    return round((perf_counter() - started) * 1000)
