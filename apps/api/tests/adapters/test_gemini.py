import base64
import json
from decimal import Decimal
from typing import Any

import httpx2
import pytest

from jalada.modules.pipeline.adapters.models.gemini import BASE_URL, GeminiModel
from jalada.modules.pipeline.adapters.models.pricing import Pricing
from jalada.modules.pipeline.domain.model import ImageInput, ModelFailed

SCHEMA = {"type": "object", "properties": {"amount_ksh": {"type": "string"}}}
PRICING = Pricing(Decimal("0.30"), Decimal("2.50"))


def gemini_answer(
    data: Any, prompt: int = 1000, output: int = 200, thoughts: int = 50
) -> dict[str, Any]:
    return {
        "candidates": [{"content": {"parts": [{"text": json.dumps(data)}]}}],
        "usageMetadata": {
            "promptTokenCount": prompt,
            "candidatesTokenCount": output,
            "thoughtsTokenCount": thoughts,
        },
    }


def model_answering(status: int, body: Any, seen: list[httpx2.Request]) -> GeminiModel:
    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        return httpx2.Response(status, json=body)

    client = httpx2.Client(transport=httpx2.MockTransport(handler), base_url=BASE_URL)
    return GeminiModel("test-key", "gemini-test", PRICING, client)


def test_the_request_asks_for_json_matching_the_schema() -> None:
    seen: list[httpx2.Request] = []
    model = model_answering(200, gemini_answer({"amount_ksh": "250.00"}), seen)

    model.complete("instructions", "Evidence text", SCHEMA)

    request = seen[0]
    body = json.loads(request.content)
    assert request.url.path.endswith("/models/gemini-test:generateContent")
    assert request.headers["x-goog-api-key"] == "test-key"
    assert "test-key" not in str(request.url), "the key travels in a header, not the address"
    assert body["systemInstruction"]["parts"][0]["text"] == "instructions"
    assert body["generationConfig"]["responseJsonSchema"] == SCHEMA
    assert body["generationConfig"]["temperature"] == 0


def test_a_photo_is_sent_inline() -> None:
    seen: list[httpx2.Request] = []
    model = model_answering(200, gemini_answer({}), seen)

    model.complete(
        "i", "The evidence is the photo.", SCHEMA, ImageInput(b"jpeg-bytes", "image/jpeg")
    )

    inline = json.loads(seen[0].content)["contents"][0]["parts"][1]["inlineData"]
    assert inline["mimeType"] == "image/jpeg"
    assert base64.b64decode(inline["data"]) == b"jpeg-bytes"


def test_the_reply_and_its_cost_are_read_back() -> None:
    model = model_answering(200, gemini_answer({"amount_ksh": "250.00"}), [])

    reply = model.complete("i", "c", SCHEMA)

    assert reply.data == {"amount_ksh": "250.00"}
    assert (reply.usage.input_tokens, reply.usage.output_tokens) == (1000, 250)
    # 1000 x 0.30 + 250 x 2.50, per million tokens
    assert reply.usage.cost_usd == Decimal("0.000925")
    assert model.name == "gemini/gemini-test"


@pytest.mark.parametrize(
    ("status", "body"),
    [
        (429, {"error": {"message": "quota for Ksh 1,000 receipt"}}),
        (500, {}),
        (200, {"candidates": []}),
        (200, {"candidates": [{"content": {"parts": [{"text": "not json"}]}}]}),
        (200, {"candidates": [{"content": {"parts": [{"text": "[1, 2]"}]}}]}),
    ],
)
def test_failures_become_model_failed_without_the_providers_message(
    status: int, body: dict[str, Any]
) -> None:
    model = model_answering(status, body, [])

    with pytest.raises(ModelFailed) as failure:
        model.complete("i", "c", SCHEMA)

    assert "Ksh" not in str(failure.value)


def test_a_timeout_becomes_model_failed() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ReadTimeout("slow", request=request)

    client = httpx2.Client(transport=httpx2.MockTransport(handler), base_url=BASE_URL)

    with pytest.raises(ModelFailed):
        GeminiModel("k", "m", PRICING, client).complete("i", "c", SCHEMA)
