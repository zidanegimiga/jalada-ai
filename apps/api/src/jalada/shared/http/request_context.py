"""Gives every request an id, binds it to every log line, and logs one line per request."""

import logging
import re
import time
import uuid
from typing import Any

import structlog
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger("jalada.http")

REQUEST_ID_HEADER = "x-request-id"
# An id from a proxy or the web app is kept only if it is plainly an id.
SAFE_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{8,128}$")


class RequestContext:
    """ASGI middleware. Logs the route pattern, never the path, so ids in addresses and
    query strings stay out of the logs."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request_id = _request_id(scope)
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        started = time.perf_counter()
        status = 500

        async def send_with_id(message: Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                message["headers"] = [
                    *message.get("headers", []),
                    (REQUEST_ID_HEADER.encode(), request_id.encode()),
                ]
            await send(message)

        try:
            await self.app(scope, receive, send_with_id)
        finally:
            logger.info("request", extra=_summary(scope, status, started))
            structlog.contextvars.clear_contextvars()


def _request_id(scope: Scope) -> str:
    for name, value in scope.get("headers", []):
        if name == REQUEST_ID_HEADER.encode():
            incoming: str = value.decode("latin-1")
            if SAFE_REQUEST_ID.match(incoming):
                return incoming
    return uuid.uuid4().hex


def _summary(scope: Scope, status: int, started: float) -> dict[str, Any]:
    route = scope.get("route")
    return {
        "method": scope["method"],
        "route": getattr(route, "path", "unmatched"),
        "status": status,
        "duration_ms": round((time.perf_counter() - started) * 1000),
        "user_id": scope.get("state", {}).get("user_id"),
    }
