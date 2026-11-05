import base64
import json
from decimal import Decimal
from typing import Any

import httpx2
import pytest

from jalada.adapters.models.ollama import OllamaModel
from jalada.pipeline.model import ImageInput, ModelFailed

SCHEMA = {"type": "object", "properties": {"amount_ksh": {"type": "string"}}}


def model_answering(status: int, body: Any, seen: list[httpx2.Request]) -> OllamaModel:
    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        return httpx2.Response(status, json=body)

    client = httpx2.Client(transport=httpx2.MockTransport(handler), base_url="http://ollama:11434")
    return OllamaModel("http://ollama:11434", "test-vision", client)


def ollama_answer(data: Any) -> dict[str, Any]:
    return {"message": {"content": json.dumps(data)}, "prompt_eval_count": 800, "eval_count": 90}


def test_the_request_asks_for_json_matching_the_schema_with_the_photo() -> None:
    seen: list[httpx2.Request] = []
    model = model_answering(200, ollama_answer({"amount_ksh": "250.00"}), seen)

    model.complete(
        "instructions", "The evidence is the photo.", SCHEMA, ImageInput(b"jpeg", "image/jpeg")
    )

    body = json.loads(seen[0].content)
    assert seen[0].url.path == "/api/chat"
    assert body["model"] == "test-vision"
    assert body["format"] == SCHEMA
    assert body["stream"] is False
    assert body["messages"][0] == {"role": "system", "content": "instructions"}
    assert base64.b64decode(body["messages"][1]["images"][0]) == b"jpeg"


def test_the_reply_is_read_back_and_costs_nothing() -> None:
    reply = model_answering(200, ollama_answer({"amount_ksh": "250.00"}), []).complete(
        "i", "c", SCHEMA
    )

    assert reply.data == {"amount_ksh": "250.00"}
    assert (reply.usage.input_tokens, reply.usage.output_tokens) == (800, 90)
    assert reply.usage.cost_usd == Decimal(0)


@pytest.mark.parametrize(
    ("status", "body"),
    [
        (404, {"error": "model 'test-vision' not found"}),
        (200, {"message": {"content": "not json"}}),
        (200, {"message": {}}),
    ],
)
def test_failures_become_model_failed(status: int, body: dict[str, Any]) -> None:
    with pytest.raises(ModelFailed):
        model_answering(status, body, []).complete("i", "c", SCHEMA)
