"""Turning HTTP errors from any model provider into the failure kinds the chain acts on."""

from collections.abc import Callable

import httpx2

from jalada.core.resilience.failures import FailureKind, ProviderFailure

UNAVAILABLE_STATUSES = {500, 502, 503, 504}
MISCONFIGURED_STATUSES = {401, 402, 403, 404}
# Phrases providers use when the input is longer than the model accepts.
TOO_LARGE_HINTS = (
    "context length",
    "context_length",
    "too many tokens",
    "token limit",
    "exceeds the maximum",
    "maximum context",
)


def send(request: Callable[[], httpx2.Response]) -> httpx2.Response:
    """Runs the request, raising ProviderFailure for anything but a success."""
    try:
        response = request()
    except httpx2.TimeoutException as error:
        raise ProviderFailure(FailureKind.TIMEOUT) from error
    except httpx2.TransportError as error:
        raise ProviderFailure(FailureKind.UNAVAILABLE) from error
    if response.is_success:
        return response
    raise failure_for(response)


def failure_for(response: httpx2.Response) -> ProviderFailure:
    status = response.status_code
    if status == 429:
        return ProviderFailure(FailureKind.RATE_LIMITED, retry_after_seconds(response))
    if status in UNAVAILABLE_STATUSES:
        return ProviderFailure(FailureKind.UNAVAILABLE, retry_after_seconds(response))
    if status in MISCONFIGURED_STATUSES:
        return ProviderFailure(FailureKind.MISCONFIGURED)
    # The body is read only to spot a too-long input; it is never logged or kept.
    if any(hint in response.text.lower() for hint in TOO_LARGE_HINTS):
        return ProviderFailure(FailureKind.TOO_LARGE)
    return ProviderFailure(FailureKind.MISCONFIGURED)


def retry_after_seconds(response: httpx2.Response) -> float | None:
    """From a Retry-After header, or Google's RetryInfo detail such as "12s"."""
    header = response.headers.get("retry-after")
    if header and header.replace(".", "", 1).isdigit():
        return float(header)
    try:
        body = response.json()
    except ValueError:
        return None
    # Bodies differ by provider: an object with details, a plain string, or nothing.
    error = body.get("error") if isinstance(body, dict) else None
    details = error.get("details") if isinstance(error, dict) else None
    for detail in details if isinstance(details, list) else []:
        delay = detail.get("retryDelay") if isinstance(detail, dict) else None
        if isinstance(delay, str) and delay.endswith("s"):
            try:
                return float(delay[:-1])
            except ValueError:
                return None
    return None
