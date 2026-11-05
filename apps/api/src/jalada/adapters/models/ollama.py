import base64
import json
from typing import Any

import httpx2

from jalada.adapters.models.pricing import Pricing
from jalada.pipeline.model import ImageInput, ModelFailed, ModelReply


class OllamaModel:
    """A local model served by Ollama. Free to run, and nothing leaves the machine."""

    def __init__(self, base_url: str, model: str, client: httpx2.Client | None = None) -> None:
        self.name = f"ollama/{model}"
        self._model = model
        # Local models can be slow on a laptop, so the timeout is generous.
        self._client = client or httpx2.Client(base_url=base_url, timeout=300)

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
        try:
            response = self._client.post("/api/chat", json=body)
            response.raise_for_status()
            payload = response.json()
            data = json.loads(payload["message"]["content"])
            if not isinstance(data, dict):
                raise ValueError("Expected a JSON object")
        except (httpx2.HTTPError, ValueError, KeyError, TypeError) as error:
            raise ModelFailed(type(error).__name__) from error
        usage = Pricing().usage(payload.get("prompt_eval_count", 0), payload.get("eval_count", 0))
        return ModelReply(data, usage)
