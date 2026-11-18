"""Each turn as OpenTelemetry spans, named as the GenAI semantic conventions name them.

    invoke_agent jalada-assistant
      chat <model>            one per model call, with its tokens
      execute_tool <tool>     one per lookup

Spans are built after the turn from its recorded steps, so the graph needs no tracing code.
They carry names, outcomes, tokens and times. Never the question, the records, the answer
or the person's id: the conversation id is enough to find the turn in the app's own tables.
"""

import logging
from datetime import datetime, timedelta

from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter
from opentelemetry.trace import Span, Tracer, set_span_in_context
from opentelemetry.util.types import AttributeValue

from jalada.modules.agent.application.ports import AgentRun
from jalada.modules.agent.domain.run import AgentStep, Outcome, StepKind
from jalada.modules.pipeline.domain.model import ModelUsage

logger = logging.getLogger(__name__)

AGENT = "jalada-assistant"


class OpenTelemetryTracer:
    def __init__(self, tracer: Tracer) -> None:
        self._tracer = tracer

    def record(self, run: AgentRun) -> None:
        try:
            self._record(run)
        except Exception:
            # Tracing must never cost the person their answer.
            logger.warning("Could not trace an assistant turn", exc_info=True)

    def _record(self, run: AgentRun) -> None:
        usage = sum((step.usage for step in run.steps), ModelUsage())
        root = self._tracer.start_span(
            f"invoke_agent {AGENT}",
            start_time=_ns(run.started_at),
            attributes={
                "gen_ai.operation.name": "invoke_agent",
                "gen_ai.agent.name": AGENT,
                "gen_ai.conversation.id": str(run.thread_id),
                "jalada.run.id": str(run.id),
                "jalada.outcome": run.outcome,
                "gen_ai.usage.input_tokens": usage.input_tokens,
                "gen_ai.usage.output_tokens": usage.output_tokens,
                "jalada.cost_usd": float(usage.cost_usd),
            },
        )
        at = run.started_at
        for step in run.steps:
            at = self._step(root, step, at)
        if run.outcome != Outcome.ANSWERED:
            root.set_attribute("error.type", run.outcome)
        root.end(end_time=_ns(run.finished_at))

    def _step(self, root: Span, step: AgentStep, at: datetime) -> datetime:
        ends = at + timedelta(milliseconds=step.duration_ms)
        attributes: dict[str, AttributeValue]
        if step.kind == StepKind.MODEL:
            name = f"chat {step.name}"
            attributes = {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": step.name,
                "gen_ai.usage.input_tokens": step.usage.input_tokens,
                "gen_ai.usage.output_tokens": step.usage.output_tokens,
                "jalada.step.outcome": step.outcome,
            }
        else:
            name = f"execute_tool {step.name}"
            attributes = {
                "gen_ai.operation.name": "execute_tool",
                "gen_ai.tool.name": step.name,
                "jalada.step.outcome": step.outcome,
            }
        span = self._tracer.start_span(
            name, context=set_span_in_context(root), start_time=_ns(at), attributes=attributes
        )
        if step.outcome in {"failed", "unusable"}:
            span.set_attribute("error.type", step.outcome)
        span.end(end_time=_ns(ends))
        return ends


def otlp_tracer(endpoint: str, headers: dict[str, str], version: str) -> OpenTelemetryTracer:
    """Sends spans in batches to an OTLP endpoint, such as Langfuse or Grafana Cloud."""
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

    return exporting_tracer(OTLPSpanExporter(endpoint=endpoint, headers=headers), version)


def exporting_tracer(exporter: SpanExporter, version: str) -> OpenTelemetryTracer:
    resource = Resource.create({"service.name": "jalada-api", "service.version": version})
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    return OpenTelemetryTracer(provider.get_tracer("jalada.assistant"))


def _ns(moment: datetime) -> int:
    return int(moment.timestamp() * 1_000_000_000)
