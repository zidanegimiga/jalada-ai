import logging

import httpx2
import pytest

from jalada.config.logging import configure_logging


def test_http_libraries_never_log_request_addresses(caplog: pytest.LogCaptureFixture) -> None:
    configure_logging("INFO")
    client = httpx2.Client(
        transport=httpx2.MockTransport(lambda request: httpx2.Response(200)),
        base_url="https://api.telegram.org",
    )

    with caplog.at_level(logging.INFO):
        client.post("/bot000:secret-token/sendMessage")

    assert "secret-token" not in caplog.text
    assert logging.getLogger("httpx2").level == logging.WARNING
