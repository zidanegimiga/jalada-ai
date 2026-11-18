import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from jalada.modules.agent.adapters.telemetry import OpenTelemetryTracer
from jalada.modules.agent.application.ports import AgentRun
from jalada.modules.agent.domain.run import AgentStep, Outcome, StepKind
from jalada.modules.agent.wiring import build_tracer
from jalada.modules.pipeline.domain.model import ModelUsage

STARTED = datetime(2026, 11, 18, 9, 0, tzinfo=UTC)
USER = uuid.uuid4()


def traced(run: AgentRun) -> InMemorySpanExporter:
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    OpenTelemetryTracer(provider.get_tracer("test")).record(run)
    return exporter


def a_run(outcome: Outcome = Outcome.ANSWERED) -> AgentRun:
    steps = (
        AgentStep(
            StepKind.MODEL,
            "gemini-3.5-flash-lite",
            "tool",
            400,
            ModelUsage(300, 40, Decimal("0.0001")),
        ),
        AgentStep(StepKind.TOOL, "add_up_payments", "ok", 20),
        AgentStep(
            StepKind.MODEL,
            "gemini-3.5-flash-lite",
            "answer",
            500,
            ModelUsage(600, 50, Decimal("0.0002")),
        ),
    )
    return AgentRun(
        uuid.uuid4(), USER, uuid.uuid4(), outcome, steps, STARTED, STARTED + timedelta(seconds=1)
    )


def test_a_turn_becomes_an_agent_span_with_a_child_per_step() -> None:
    run = a_run()

    spans = traced(run).get_finished_spans()

    names = [span.name for span in spans]
    assert names == [
        "chat gemini-3.5-flash-lite",
        "execute_tool add_up_payments",
        "chat gemini-3.5-flash-lite",
        "invoke_agent jalada-assistant",
    ]
    root = spans[-1]
    assert root.attributes is not None
    assert root.attributes["gen_ai.usage.input_tokens"] == 900
    assert root.attributes["gen_ai.conversation.id"] == str(run.thread_id)
    assert all(
        span.parent is not None and span.parent.span_id == root.context.span_id
        for span in spans[:-1]
    )


def test_steps_follow_each_other_in_time() -> None:
    spans = traced(a_run()).get_finished_spans()

    first, tool, second = spans[:3]
    assert first.start_time == int(STARTED.timestamp() * 1e9)
    assert tool.start_time == first.end_time
    assert second.start_time == tool.end_time


def test_traces_never_hold_the_person_or_what_was_said() -> None:
    spans = traced(a_run()).get_finished_spans()

    for span in spans:
        values = [str(v) for v in (span.attributes or {}).values()]
        assert str(USER) not in values


def test_a_turn_that_did_not_answer_is_marked_as_an_error() -> None:
    root = traced(a_run(Outcome.WITHHELD)).get_finished_spans()[-1]

    assert root.attributes is not None
    assert root.attributes["error.type"] == "withheld"


def test_no_traces_url_means_no_tracing() -> None:
    assert type(build_tracer(None, None, "dev")).__name__ == "NoTracing"


def test_bad_trace_headers_stop_startup() -> None:
    with pytest.raises(ValueError, match="JALADA_AGENT_TRACES_HEADERS"):
        build_tracer("https://otel.example.com/v1/traces", "[1]", "dev")
