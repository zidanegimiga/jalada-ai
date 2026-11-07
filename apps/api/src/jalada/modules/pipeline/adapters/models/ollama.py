import base64
import json
from typing import Any

import httpx2

from jalada.core.resilience.failures import FailureKind, ProviderFailure
from jalada.modules.pipeline.adapters.models.http_failures import send
from jalada.modules.pipeline.adapters.models.pricing import Pricing
from jalada.modules.pipeline.adapters.models.profiles import ModelProfile, ProviderAccount
from jalada.modules.pipeline.adapters.models.registry import provider
from jalada.modules.pipeline.domain.model import ImageInput, ModelReply

DEFAULT_URL = "http://localhost:11434"


class OllamaModel:
    """A local model served by Ollama. Free to run, and nothing leaves the machine."""

    def __init__(
        self, base_url: str, model: str, client: httpx2.Client | None = None, timeout: float = 300
    ) -> None:
        self.name = f"ollama/{model}"
        self._model = model
        # Local models can be slow on a laptop, so the default timeout is generous.
        self._client = client or httpx2.Client(base_url=base_url, timeout=timeout)

    def complete(
        self,
        instructions: str,
        content: str,
        schema: dict[str, Any],
        image: ImageInput | None = None,
    ) -> ModelReply:
        message: dict[str, Any] = {"role": "user", "content": content}
        if image:
            message["images"] = [base64.b64encode(image.data).decode()]
        body = {
            "model": self._model,
            "messages": [{"role": "system", "content": instructions}, message],
            "format": schema,
            "stream": False,
            "options": {"temperature": 0},
        }
        payload = send(lambda: self._client.post("/api/chat", json=body)).json()
        try:
            data = json.loads(payload["message"]["content"])
        except (ValueError, KeyError, TypeError) as error:
            raise ProviderFailure(FailureKind.BAD_OUTPUT) from error
        if not isinstance(data, dict):
            raise ProviderFailure(FailureKind.BAD_OUTPUT)
        usage = Pricing().usage(payload.get("prompt_eval_count", 0), payload.get("eval_count", 0))
        return ModelReply(data, usage)


@provider("ollama")
def ollama(profile: ModelProfile, account: ProviderAccount) -> OllamaModel:
    return OllamaModel(
        account.base_url or DEFAULT_URL, profile.model, timeout=profile.timeout_seconds
    )
