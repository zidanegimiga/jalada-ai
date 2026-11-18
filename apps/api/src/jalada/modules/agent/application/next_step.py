"""How the model says what it wants to do next: one JSON object per step.

Any model in the catalogue can answer in JSON that matches a schema, so the same loop works
on Gemini, Ollama and OpenAI-compatible providers without native tool calling. A tool's
arguments travel as a JSON string, because each tool's arguments differ and some providers
only accept schemas with fixed fields.
"""

import json
from typing import Any

from jalada.modules.agent.application.tools import BadArguments, ToolRegistry
from jalada.modules.agent.domain.actions import Answer, Decision, ToolCall

NEXT_STEP_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": ["tool", "answer"]},
        "tool": {"type": ["string", "null"]},
        "arguments": {"type": ["string", "null"]},
        "answer": {"type": ["string", "null"]},
    },
    "required": ["action", "tool", "arguments", "answer"],
}


class Unusable(Exception):
    """The reply cannot be acted on. The message is shown to the model so it can correct it."""


def read_decision(data: dict[str, Any], tools: ToolRegistry) -> Decision:
    if data.get("action") == "answer":
        text = (data.get("answer") or "").strip()
        if not text:
            raise Unusable("The answer was empty.")
        return Answer(text)
    tool = tools.get(data.get("tool") or "")
    if tool is None:
        raise Unusable(f"There is no tool called {data.get('tool')!r}.")
    try:
        arguments = json.loads(data.get("arguments") or "{}")
    except json.JSONDecodeError:
        raise Unusable("The arguments were not a JSON object.") from None
    if not isinstance(arguments, dict):
        raise Unusable("The arguments were not a JSON object.")
    try:
        parsed = tool.parse(arguments)
    except BadArguments as error:
        raise Unusable(str(error)) from None
    return ToolCall(tool.name, parsed.model_dump(mode="json"))
