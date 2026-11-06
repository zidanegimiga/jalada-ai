import io
import json
import logging
from collections.abc import Iterator

import httpx2
import pytest
import structlog

from jalada.config.logging import configure_logging, log_context


@pytest.fixture
def lines() -> Iterator[io.StringIO]:
    """JSON log output, with the logging setup put back afterwards."""
    root = logging.getLogger()
    saved = (list(root.handlers), root.level)
    stream = io.StringIO()
    configure_logging("INFO", json_lines=True, stream=stream)
    yield stream
    root.handlers, root.level = saved
    structlog.contextvars.clear_contextvars()


def records(stream: io.StringIO) -> list[dict[str, object]]:
    return [json.loads(line) for line in stream.getvalue().splitlines()]


def test_records_are_json_with_the_bound_request_id(lines: io.StringIO) -> None:
    structlog.contextvars.bind_contextvars(request_id="req-123456")

    logging.getLogger("jalada.test").warning("storage check failed with %s", "Timeout")

    [record] = records(lines)
    assert record["event"] == "storage check failed with Timeout"
    assert record["level"] == "warning"
    assert record["logger"] == "jalada.test"
    assert record["request_id"] == "req-123456"
    assert "timestamp" in record


def test_sensitive_fields_are_never_written(lines: io.StringIO) -> None:
    logging.getLogger("jalada.test").info(
        "saved", extra={"amount_cents": 15000, "counterparty": "JANE", "route": "/v1/entries"}
    )

    [record] = records(lines)
    assert record["amount_cents"] == record["counterparty"] == "[removed]"
    assert record["route"] == "/v1/entries"


def test_exceptions_keep_their_type_and_place_but_not_their_message(
    lines: io.StringIO,
) -> None:
    try:
        raise ValueError("Key (mpesa_code)=(UK5AB1CD23) already exists")
    except ValueError:
        logging.getLogger("jalada.test").exception("saving failed")

    text = lines.getvalue()
    [record] = records(lines)
    assert record["error"]["type"] == "ValueError"  # type: ignore[index]
    assert "test_logging.py" in record["error"]["frames"][0]  # type: ignore[index]
    assert "UK5AB1CD23" not in text


def test_http_libraries_never_log_request_addresses(lines: io.StringIO) -> None:
    client = httpx2.Client(
        transport=httpx2.MockTransport(lambda request: httpx2.Response(200)),
        base_url="https://api.telegram.org",
    )

    client.post("/bot000:secret-token/sendMessage")

    assert "secret-token" not in lines.getvalue()
    assert logging.getLogger("httpx2").level == logging.WARNING


def test_setting_up_twice_keeps_one_handler(lines: io.StringIO) -> None:
    configure_logging("INFO", json_lines=True, stream=lines)

    logging.getLogger("jalada.test").warning("once")

    assert len(records(lines)) == 1


def test_log_context_adds_values_only_inside_the_block(lines: io.StringIO) -> None:
    log = logging.getLogger("jalada.test")

    with log_context(job_id=7, job_kind="process_evidence"):
        log.warning("inside")
    log.warning("outside")

    inside, outside = records(lines)
    assert inside["job_id"] == 7 and inside["job_kind"] == "process_evidence"
    assert "job_id" not in outside
