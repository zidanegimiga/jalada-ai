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


class OpenAICompatibleModel:
    """Any provider that speaks the OpenAI chat completions API: OpenAI itself, OpenRouter,
    Groq, Together, DeepSeek, Mistral, a vLLM server and others. Which one is set by the
    account's base_url, so a new provider of this kind needs no new code."""

    def __init__(self, name: str, model: str, pricing: Pricing, client: httpx2.Client) -> None:
        self.name = name
        self._model = model
        self._pricing = pricing
        self._client = client

    def complete(
        self,
        instructions: str,
        content: str,
        schema: dict[str, Any],
        image: ImageInput | None = None,
    ) -> ModelReply:
        parts: list[dict[str, Any]] = [{"type": "text", "text": content}]
        if image:
            encoded = base64.b64encode(image.data).decode()
            url = f"data:{image.content_type};base64,{encoded}"
            parts.append({"type": "image_url", "image_url": {"url": url}})
        body = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": instructions},
                {"role": "user", "content": parts},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "answer", "schema": schema},
            },
            "temperature": 0,
        }
        payload = send(lambda: self._client.post("/chat/completions", json=body)).json()
        return self._reply(payload)

    def _reply(self, payload: dict[str, Any]) -> ModelReply:
        try:
            choice = payload["choices"][0]
            finish = choice.get("finish_reason")
            if finish == "content_filter":
                raise ProviderFailure(FailureKind.REFUSED)
            if finish == "length":
                raise ProviderFailure(FailureKind.BAD_OUTPUT)
            data = json.loads(choice["message"]["content"])
        except (ValueError, KeyError, IndexError, TypeError) as error:
            raise ProviderFailure(FailureKind.BAD_OUTPUT) from error
        if not isinstance(data, dict):
            raise ProviderFailure(FailureKind.BAD_OUTPUT)
        usage = payload.get("usage", {})
        tokens = (usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))
        return ModelReply(data, self._pricing.usage(*tokens))


@provider("openai_compatible")
def openai_compatible(profile: ModelProfile, account: ProviderAccount) -> OpenAICompatibleModel:
    if not account.base_url:
        raise ModelSetupError(f"{profile.name}: the {profile.account!r} account needs a base_url")
    headers = {"Authorization": f"Bearer {account.api_key}"} if account.api_key else {}
    client = httpx2.Client(
        base_url=account.base_url, headers=headers, timeout=profile.timeout_seconds
    )
    pricing = Pricing(profile.input_price, profile.output_price)
    name = f"{profile.account}/{profile.model}"
    return OpenAICompatibleModel(name, profile.model, pricing, client)
