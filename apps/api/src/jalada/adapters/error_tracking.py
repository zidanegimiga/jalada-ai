"""Sends errors to Sentry, with anything personal or financial taken out first.

Nothing is sent unless a DSN is set. No request bodies, headers, cookies, query strings,
local variables or exception messages ever leave the server: an exception message can
repeat what caused it, such as an amount or an M-Pesa code.
"""

from typing import Any
from urllib.parse import urlsplit

import sentry_sdk
from sentry_sdk.transport import Transport
from sentry_sdk.types import Breadcrumb, BreadcrumbHint, Event, Hint

from jalada.config.logging import REMOVED, SENSITIVE_KEYS


def start_error_tracking(
    dsn: str | None, environment: str, release: str, transport: type[Transport] | None = None
) -> bool:
    """True if errors will be sent. `transport` is for tests."""
    if not dsn:
        return False
    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        release=release,
        # No personal data is collected while data_collection is left unset (the default).
        include_local_variables=False,
        max_request_body_size="never",
        # Errors only. Tracing is a separate decision.
        traces_sample_rate=0.0,
        before_send=scrub_event,
        before_breadcrumb=scrub_breadcrumb,
        transport=transport,
    )
    return True


def scrub_event(event: Event, _: Hint) -> Event:
    request = event.get("request")
    if request:
        event["request"] = {"method": request.get("method"), "url": _path_only(request.get("url"))}
    for exception in event.get("exception", {}).get("values", []):
        exception["value"] = REMOVED
    event.pop("user", None)
    _remove_sensitive(event.get("extra"))
    breadcrumbs = event.get("breadcrumbs")
    for crumb in breadcrumbs.get("values", []) if isinstance(breadcrumbs, dict) else []:
        scrub_breadcrumb(crumb, None)
    return event


def scrub_breadcrumb(crumb: Breadcrumb, _: BreadcrumbHint | None) -> Breadcrumb:
    data = crumb.get("data")
    if isinstance(data, dict):
        # Outgoing calls: Telegram's addresses carry the bot token, so keep only the host.
        if "url" in data:
            data["url"] = _host_only(data["url"])
        for key in ("http.query", "http.fragment"):
            data.pop(key, None)
        _remove_sensitive(data)
    return crumb


def _remove_sensitive(values: Any) -> None:
    if isinstance(values, dict):
        for key in SENSITIVE_KEYS.intersection(values):
            values[key] = REMOVED


def _path_only(url: Any) -> Any:
    if not isinstance(url, str):
        return url
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}{parts.path}"


def _host_only(url: Any) -> Any:
    if not isinstance(url, str):
        return url
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}" if parts.netloc else REMOVED
