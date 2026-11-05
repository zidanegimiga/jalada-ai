import base64
import json
from typing import Any

import httpx2

from jalada.adapters.models.pricing import Pricing
from jalada.pipeline.model import ImageInput, ModelFailed, ModelReply

BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


class GeminiModel:
    """Google Gemini through its REST API, answering in JSON that matches a schema."""

    def __init__(
        self,
        api_key: str,
        model: str,
        pricing: Pricing,
        client: httpx2.Client | None = None,
    ) -> None:
        self.name = f"gemini/{model}"
        self._model = model
        self._pricing = pricing
        self._client = client or httpx2.Client(base_url=BASE_URL, timeout=60)
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
        try:
            response = self._client.post(
                f"/models/{self._model}:generateContent", json=body, headers=self._headers
            )
            response.raise_for_status()
            return self._reply(response.json())
        except (httpx2.HTTPError, ValueError, KeyError, IndexError, TypeError) as error:
            # The error type only: provider messages can echo the evidence back.
            raise ModelFailed(type(error).__name__) from error

    def _reply(self, payload: dict[str, Any]) -> ModelReply:
        text = payload["candidates"][0]["content"]["parts"][0]["text"]
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError("Expected a JSON object")
        usage = payload.get("usageMetadata", {})
        output = usage.get("candidatesTokenCount", 0) + usage.get("thoughtsTokenCount", 0)
        return ModelReply(data, self._pricing.usage(usage.get("promptTokenCount", 0), output))
