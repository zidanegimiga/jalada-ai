import json
from decimal import Decimal
from typing import Any

import httpx2
import pytest

from jalada.core.resilience.failures import FailureKind, ProviderFailure
from jalada.modules.pipeline.adapters.models.openai_compatible import OpenAICompatibleModel
from jalada.modules.pipeline.adapters.models.pricing import Pricing
from jalada.modules.pipeline.domain.model import ImageInput

SCHEMA = {"type": "object", "properties": {"amount_ksh": {"type": "string"}}}
URL = "https://router.example.com/v1"


def model_answering(response: httpx2.Response, seen: list[httpx2.Request]) -> OpenAICompatibleModel:
    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        return response

    client = httpx2.Client(transport=httpx2.MockTransport(handler), base_url=URL)
    pricing = Pricing(Decimal("1.00"), Decimal("2.00"))
    return OpenAICompatibleModel("router/m", "vendor/m", pricing, client)


def answer(content: str, finish: str = "stop") -> dict[str, Any]:
    return {
        "choices": [{"message": {"content": content}, "finish_reason": finish}],
        "usage": {"prompt_tokens": 1000, "completion_tokens": 100},
    }


def test_the_request_asks_for_json_matching_the_schema_with_the_photo() -> None:
    seen: list[httpx2.Request] = []
    model = model_answering(httpx2.Response(200, json=answer('{"amount_ksh": "1.00"}')), seen)

    reply = model.complete("rules", "text", SCHEMA, ImageInput(b"\xff\xd8", "image/jpeg"))

    body = json.loads(seen[0].content)
    assert seen[0].url.path == "/v1/chat/completions"
    assert body["model"] == "vendor/m"
    assert body["response_format"]["json_schema"]["schema"] == SCHEMA
    assert body["messages"][1]["content"][1]["image_url"]["url"].startswith("data:image/jpeg")
    assert reply.data == {"amount_ksh": "1.00"}
    # 1000 x 1.00 + 100 x 2.00, per million tokens
    assert reply.usage.cost_usd == Decimal("0.0012")


@pytest.mark.parametrize(
    ("response", "kind"),
    [
        (httpx2.Response(429, headers={"Retry-After": "5"}), FailureKind.RATE_LIMITED),
        (
            httpx2.Response(400, json={"error": {"code": "context_length_exceeded"}}),
            FailureKind.TOO_LARGE,
        ),
        (httpx2.Response(401, json={"error": {"message": "bad key"}}), FailureKind.MISCONFIGURED),
        (httpx2.Response(502), FailureKind.UNAVAILABLE),
        (httpx2.Response(200, json=answer("{}", "content_filter")), FailureKind.REFUSED),
        (httpx2.Response(200, json=answer('{"a": 1', "length")), FailureKind.BAD_OUTPUT),
        (httpx2.Response(200, json=answer("not json")), FailureKind.BAD_OUTPUT),
    ],
)
def test_each_failure_has_a_kind(response: httpx2.Response, kind: FailureKind) -> None:
    with pytest.raises(ProviderFailure) as failure:
        model_answering(response, []).complete("i", "c", SCHEMA)

    assert failure.value.kind == kind
    if kind == FailureKind.RATE_LIMITED:
        assert failure.value.retry_after == 5.0
