import json
import logging
from collections.abc import Iterator
from typing import Any

import pytest
import sentry_sdk
from conftest import make_settings
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sentry_sdk.envelope import Envelope
from sentry_sdk.transport import Transport

from jalada.builders import start_error_tracking_from
from jalada.core.error_tracking import scrub_breadcrumb, scrub_event, start_error_tracking

DSN = "https://public@errors.example.com/1"
# Built at runtime: Sentry sends the source lines around each frame, and these must only
# be able to reach an event through the data, never by being written in the code.
NAME = "".join(["JANE", " WANJIKU"])
AMOUNT = "".join(["Ksh", " 1,500"])
PHONE = "".join(["0712", "345678"])
CODE = "".join(["UK5AB", "1CD23"])
SESSION = "".join(["session-", "value-123"])
BEARER = "".join(["Bearer ", "abc123"])


class Captured(Transport):
    """Keeps what would have been sent to Sentry."""

    events: list[dict[str, Any]] = []

    def capture_envelope(self, envelope: Envelope) -> None:
        event = envelope.get_event()
        if event is not None:
            # Through JSON, as it would be sent.
            Captured.events.append(json.loads(json.dumps(event, default=str)))


@pytest.fixture
def sent() -> Iterator[list[dict[str, Any]]]:
    Captured.events = []
    assert start_error_tracking(DSN, "production", "abc1234", transport=Captured)
    yield Captured.events
    sentry_sdk.get_client().close()
    sentry_sdk.get_global_scope().set_client(None)


def test_nothing_starts_without_a_dsn() -> None:
    assert start_error_tracking(None, "production", "abc1234") is False
    assert start_error_tracking("", "production", "abc1234") is False


def test_a_crash_in_a_request_is_sent_without_anything_personal(
    sent: list[dict[str, Any]],
) -> None:
    app = FastAPI()

    @app.post("/v1/things/{thing_id}")
    def crash(thing_id: str) -> None:
        local_amount = AMOUNT  # noqa: F841 - a local variable that must not be sent
        raise RuntimeError(f"{AMOUNT} to {NAME}")

    TestClient(app, raise_server_exceptions=False).post(
        f"/v1/things/42?phone={PHONE}",
        json={"text": f"{CODE} Confirmed"},
        headers={"Cookie": f"jalada_session={SESSION}", "Authorization": BEARER},
    )
    sentry_sdk.flush()

    [event] = sent
    text = json.dumps(event)
    assert event["exception"]["values"][-1]["type"] == "RuntimeError"
    assert event["release"] == "abc1234" and event["environment"] == "production"
    assert event["request"] == {"method": "POST", "url": "http://testserver/v1/things/42"}
    for secret in (NAME, AMOUNT, PHONE, CODE, SESSION, BEARER):
        assert secret not in text, secret


def test_an_error_log_with_a_stack_is_sent_without_its_message(
    sent: list[dict[str, Any]],
) -> None:
    try:
        raise ConnectionError(f"storage refused {AMOUNT} receipt")
    except ConnectionError as error:
        logging.getLogger("jalada.jobs").error(
            "job failed with %s", "ConnectionError", exc_info=error
        )
    sentry_sdk.flush()

    [event] = sent
    assert event["logentry"]["formatted"] == "job failed with ConnectionError"
    assert AMOUNT not in json.dumps(event)


def test_breadcrumbs_keep_only_the_host_of_outgoing_calls() -> None:
    crumb = {
        "category": "httplib",
        "data": {
            "url": "https://api.telegram.org/bot000:secret-token/sendMessage",
            "http.query": "chat_id=1",
            "method": "POST",
        },
    }

    scrubbed = scrub_breadcrumb(crumb, None)

    assert scrubbed["data"] == {"url": "https://api.telegram.org", "method": "POST"}


def test_extra_fields_that_could_be_personal_are_removed() -> None:
    event = scrub_event({"extra": {"amount_cents": 100, "route": "/v1/x"}, "user": {"id": 1}}, {})

    assert event == {"extra": {"amount_cents": "[removed]", "route": "/v1/x"}}


def test_the_app_starts_without_error_tracking_when_no_dsn_is_set() -> None:
    assert start_error_tracking_from(make_settings()) is False
