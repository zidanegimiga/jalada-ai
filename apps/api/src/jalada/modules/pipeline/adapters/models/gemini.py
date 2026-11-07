import base64
import json
from typing import Any

import httpx2

from jalada.core.resilience.failures import FailureKind, ProviderFailure
from jalada.modules.pipeline.adapters.models.http_failures import send
from jalada.modules.pipeline.adapters.models.pricing import Pricing
from jalada.modules.pipeline.adapters.models.profiles import ModelProfile, ProviderAccount
from jalada.modules.pipeline.adapters.models.registry import ModelSetupError, provider
from jalada.modules.pipeline.domain.model import ImageInput, ModelReply

BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
# Finish reasons that mean Gemini would not answer, rather than could not.
REFUSALS = {"SAFETY", "RECITATION", "BLOCKLIST", "PROHIBITED_CONTENT", "SPII", "OTHER"}


class GeminiModel:
    """Google Gemini through its REST API, answering in JSON that matches a schema."""

    def __init__(
        self,
        api_key: str,
        model: str,
        pricing: Pricing,
        client: httpx2.Client | None = None,
        timeout: float = 60,
    ) -> None:
        self.name = f"gemini/{model}"
        self._model = model
        self._pricing = pricing
        self._client = client or httpx2.Client(base_url=BASE_URL, timeout=timeout)
        self._headers = {"x-goog-api-key": api_key}

    def complete(
        self,
        instructions: str,
        content: str,
        schema: dict[str, Any],
        image: ImageInput | None = None,
    ) -> ModelReply:
        parts: list[dict[str, Any]] = [{"text": content}]
        if image:
            encoded = base64.b64encode(image.data).decode()
            parts.append({"inlineData": {"mimeType": image.content_type, "data": encoded}})
        body = {
            "systemInstruction": {"parts": [{"text": instructions}]},
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseJsonSchema": schema,
                "temperature": 0,
            },
        }
        response = send(
            lambda: self._client.post(
                f"/models/{self._model}:generateContent", json=body, headers=self._headers
            )
        )
        return self._reply(response)

    def _reply(self, response: httpx2.Response) -> ModelReply:
        try:
            payload = response.json()
            if payload.get("promptFeedback", {}).get("blockReason"):
                raise ProviderFailure(FailureKind.REFUSED)
            candidate = payload["candidates"][0]
            finish = candidate.get("finishReason", "STOP")
            if finish in REFUSALS:
                raise ProviderFailure(FailureKind.REFUSED)
            if finish == "MAX_TOKENS":
                raise ProviderFailure(FailureKind.BAD_OUTPUT)
            data = json.loads(candidate["content"]["parts"][0]["text"])
        except (ValueError, KeyError, IndexError, TypeError) as error:
            raise ProviderFailure(FailureKind.BAD_OUTPUT) from error
        if not isinstance(data, dict):
            raise ProviderFailure(FailureKind.BAD_OUTPUT)
        usage = payload.get("usageMetadata", {})
        output = usage.get("candidatesTokenCount", 0) + usage.get("thoughtsTokenCount", 0)
        return ModelReply(data, self._pricing.usage(usage.get("promptTokenCount", 0), output))


@provider("gemini")
def gemini(profile: ModelProfile, account: ProviderAccount) -> GeminiModel:
    if not account.api_key:
        raise ModelSetupError(f"{profile.name}: the gemini account needs an api_key")
    client = httpx2.Client(base_url=account.base_url or BASE_URL, timeout=profile.timeout_seconds)
    pricing = Pricing(profile.input_price, profile.output_price)
    return GeminiModel(account.api_key, profile.model, pricing, client)
