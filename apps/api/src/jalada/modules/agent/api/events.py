"""A turn as server-sent events, so the chat can show progress before the answer.

    event: progress  data: {"stage": "looking_up", "tool": "add_up_payments", "label": "..."}
    event: answer    data: {"thread_id": "...", "text": "...", "outcome": "answered"}
    event: error     data: {"code": "...", "message": "..."}

The turn runs on its own thread and reports into a queue that the response reads from. If
the person leaves, the turn still finishes and its answer is kept in the conversation.
"""

import json
import logging
import queue
import threading
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Any

from jalada.modules.agent.application.conversations import Reply
from jalada.modules.agent.domain.progress import OnProgress, Progress

logger = logging.getLogger(__name__)

# The longest a person waits with no event before the stream gives up.
QUIET_SECONDS = 120.0
FAILED = {"code": "assistant_failed", "message": "Something went wrong. Please try again."}


@dataclass(frozen=True)
class _End:
    """Marks the end of the stream."""


def event(name: str, data: dict[str, Any]) -> str:
    return f"event: {name}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def stream_turn(ask: Callable[[OnProgress], Reply]) -> Iterator[str]:
    events: queue.Queue[str | _End] = queue.Queue()

    def on_progress(progress: Progress) -> None:
        events.put(
            event(
                "progress",
                {"stage": progress.stage, "tool": progress.tool, "label": progress.label},
            )
        )

    def run() -> None:
        try:
            reply = ask(on_progress)
            data = {"thread_id": str(reply.thread_id), "text": reply.text, "outcome": reply.outcome}
            events.put(event("answer", data))
        except Exception:
            # Logged by type only: the message can repeat the person's records.
            logger.exception("Assistant turn failed")
            events.put(event("error", FAILED))
        finally:
            events.put(_End())

    threading.Thread(target=run, name="assistant-turn", daemon=True).start()
    while True:
        try:
            item = events.get(timeout=QUIET_SECONDS)
        except queue.Empty:
            yield event("error", FAILED)
            return
        if isinstance(item, _End):
            return
        yield item
