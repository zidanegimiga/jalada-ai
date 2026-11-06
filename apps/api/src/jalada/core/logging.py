"""One log format for every logger: JSON lines in production, readable lines locally.

Code keeps using the standard `logging.getLogger`. structlog formats every record and adds
the request id and anything else bound with `structlog.contextvars.bind_contextvars`.
"""

import logging
import sys
import traceback
from collections.abc import Iterator, MutableMapping
from contextlib import contextmanager
from typing import IO, Any

import structlog

# These libraries log every request address at INFO. Telegram puts the bot token in the
# address, so their request lines must never be written.
QUIET_LIBRARIES = ("httpx", "httpx2", "httpcore", "httpcore2")
# Fields that can hold personal or financial details. Their values are never written.
SENSITIVE_KEYS = frozenset(
    {
        "amount",
        "amount_cents",
        "authorization",
        "cookie",
        "counterparty",
        "email",
        "mpesa_code",
        "password",
        "phone",
        "secret",
        "text",
        "token",
    }
)
REMOVED = "[removed]"
HANDLER_NAME = "jalada"

EventDict = MutableMapping[str, Any]


def remove_sensitive_fields(_: Any, __: str, event: EventDict) -> EventDict:
    for key in SENSITIVE_KEYS.intersection(event):
        event[key] = REMOVED
    return event


def exception_without_message(_: Any, __: str, event: EventDict) -> EventDict:
    """An exception as its type and where it was raised, never its message: messages can
    carry what caused them, such as a database row with an M-Pesa code."""
    exc_info = event.pop("exc_info", None)
    if exc_info is True:
        exc_info = sys.exc_info()
    if isinstance(exc_info, BaseException):
        exc_info = (type(exc_info), exc_info, exc_info.__traceback__)
    if isinstance(exc_info, tuple) and exc_info[0] is not None:
        frames = traceback.extract_tb(exc_info[2])
        # Not "exception": renderers expect that key to hold formatted traceback text.
        event["error"] = {
            "type": exc_info[0].__name__,
            "frames": [f"{frame.filename}:{frame.lineno} in {frame.name}" for frame in frames],
        }
    return event


SHARED_PROCESSORS: list[Any] = [
    structlog.contextvars.merge_contextvars,
    structlog.stdlib.add_log_level,
    structlog.stdlib.add_logger_name,
    structlog.stdlib.ExtraAdder(),
    structlog.processors.TimeStamper(fmt="iso", utc=True),
    remove_sensitive_fields,
    exception_without_message,
]


@contextmanager
def log_context(**values: Any) -> Iterator[None]:
    """Adds the values to every log line written inside the block, on this thread."""
    structlog.contextvars.bind_contextvars(**values)
    try:
        yield
    finally:
        structlog.contextvars.unbind_contextvars(*values)


def configure_logging(level: str, json_lines: bool, stream: IO[str] | None = None) -> None:
    """Send every log record through structlog. Safe to call more than once."""
    renderer: Any = (
        structlog.processors.JSONRenderer()
        if json_lines
        else structlog.dev.ConsoleRenderer(colors=False)
    )
    handler = logging.StreamHandler(stream or sys.stderr)
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=SHARED_PROCESSORS,
            processors=[structlog.stdlib.ProcessorFormatter.remove_processors_meta, renderer],
        )
    )
    handler.set_name(HANDLER_NAME)
    root = logging.getLogger()
    # Replace this module's handler from an earlier call, and leave any others alone.
    root.handlers = [h for h in root.handlers if h.get_name() != HANDLER_NAME] + [handler]
    root.setLevel(level)
    for name in QUIET_LIBRARIES:
        logging.getLogger(name).setLevel(logging.WARNING)
    # uvicorn's own loggers pass their records up to this handler instead of printing them.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True
