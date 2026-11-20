from collections.abc import Callable

from starlette.concurrency import run_in_threadpool
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from jalada.core.idempotency.ports import Answer, Seen
from jalada.core.idempotency.requests import (
    VALID_KEY,
    IdempotentRequests,
    fingerprint_of,
    owner_of,
)
from jalada.shared.http.errors import error_response

HEADER = "idempotency-key"
REPLAYED_HEADER = "Idempotent-Replayed"
WRITES = {"POST", "PUT", "PATCH", "DELETE"}
# Read whole before the route runs, so held to just above the largest upload (10 MB).
MAX_BODY_BYTES = 11 * 1024 * 1024

REFUSALS = {
    Seen.RUNNING: (
        409,
        "still_running",
        "The same change is still being saved. Try again in a moment.",
    ),
    Seen.DIFFERENT: (
        422,
        "idempotency_key_reused",
        "That Idempotency-Key was already used for a different request.",
    ),
}


class Idempotency:
    """ASGI middleware. A write that carries an Idempotency-Key runs once per signed-in
    session; sending it again returns the first answer instead of doing it twice. Off when
    the app's services have no idempotency set up."""

    def __init__(self, app: ASGIApp, session_token: Callable[[Request], str | None]) -> None:
        self.app = app
        self.session_token = session_token

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["method"] not in WRITES:
            await self.app(scope, receive, send)
            return
        request = Request(scope)
        requests: IdempotentRequests | None = request.app.state.services.idempotency
        key = request.headers.get(HEADER)
        token = self.session_token(request) if key is not None else None
        if requests is None or key is None or token is None:
            await self.app(scope, receive, send)
            return
        if not VALID_KEY.match(key):
            refusal = error_response(
                400, "invalid_idempotency_key", "Use up to 64 letters, digits, - or _."
            )
            await refusal(scope, receive, send)
            return
        await _Once(self.app, requests, owner_of(token), key)(scope, receive, send)


class _Once:
    """One keyed write: runs it and keeps the answer, or answers from what was kept."""

    def __init__(self, app: ASGIApp, requests: IdempotentRequests, owner: str, key: str) -> None:
        self.app = app
        self.requests = requests
        self.owner = owner
        self.key = key

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        body = await _read_body(receive)
        if body is None:
            await error_response(413, "too_large", "That is too big. Files can be up to 10 MB.")(
                scope, receive, send
            )
            return
        fingerprint = fingerprint_of(scope["method"], scope["path"], scope["query_string"], body)
        attempt = await run_in_threadpool(self.requests.begin, self.owner, self.key, fingerprint)
        if attempt.seen is Seen.NO_SESSION:
            await self.app(scope, _replay(body, receive), send)
        elif attempt.seen is Seen.ANSWERED and attempt.answer:
            await _send_again(attempt.answer)(scope, receive, send)
        elif attempt.seen in REFUSALS:
            await error_response(*REFUSALS[attempt.seen])(scope, receive, send)
        else:
            await self._run_and_keep(scope, _replay(body, receive), send)

    async def _run_and_keep(self, scope: Scope, receive: Receive, send: Send) -> None:
        recorded = _Recorder(send)
        try:
            await self.app(scope, receive, recorded)
        except BaseException:
            await run_in_threadpool(self.requests.abandon, self.owner, self.key)
            raise
        await run_in_threadpool(self.requests.finish, self.owner, self.key, recorded.answer())


class _Recorder:
    """Passes the answer on to the client, keeping a copy."""

    def __init__(self, send: Send) -> None:
        self._send = send
        self.status = 500
        self.content_type: str | None = None
        self.chunks: list[bytes] = []

    async def __call__(self, message: Message) -> None:
        if message["type"] == "http.response.start":
            self.status = message["status"]
            for name, value in message.get("headers", []):
                if name.lower() == b"content-type":
                    self.content_type = value.decode("latin-1")
        elif message["type"] == "http.response.body":
            self.chunks.append(message.get("body", b""))
        await self._send(message)

    def answer(self) -> Answer:
        return Answer(self.status, self.content_type, b"".join(self.chunks))


async def _read_body(receive: Receive) -> bytes | None:
    """The whole request body, or None once it passes the limit."""
    chunks: list[bytes] = []
    size = 0
    while True:
        message = await receive()
        if message["type"] != "http.request":
            break
        chunks.append(message.get("body", b""))
        size += len(chunks[-1])
        if size > MAX_BODY_BYTES:
            return None
        if not message.get("more_body", False):
            break
    return b"".join(chunks)


def _replay(body: bytes, receive: Receive) -> Receive:
    """Hands the body already read to the app, then listens to the client as before."""
    sent = False

    async def again() -> Message:
        nonlocal sent
        if sent:
            return await receive()
        sent = True
        return {"type": "http.request", "body": body, "more_body": False}

    return again


def _send_again(answer: Answer) -> Response:
    return Response(
        answer.body,
        status_code=answer.status,
        media_type=answer.content_type,
        headers={REPLAYED_HEADER: "true"},
    )
