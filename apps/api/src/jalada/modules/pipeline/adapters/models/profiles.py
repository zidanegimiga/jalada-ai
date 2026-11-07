"""What each model is (the catalogue) and how to reach each provider (the accounts).

Models are data, not code: adding one, or changing its price, means adding or editing an
entry in catalogue.toml, or passing extra entries in JALADA_EXTRA_MODELS. Which ones are
used, in what order, is JALADA_MODEL_CHAIN.
"""

import json
import tomllib
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any

CATALOGUE = Path(__file__).with_name("catalogue.toml")


@dataclass(frozen=True)
class ModelProfile:
    name: str
    # Which adapter talks to it: gemini, ollama, openai_compatible.
    provider: str
    # The provider's own id for the model.
    model: str
    # Which entry in JALADA_MODEL_PROVIDERS holds its key and address. Defaults to `provider`.
    account: str = ""
    vision: bool = False
    context_tokens: int = 32_000
    timeout_seconds: float = 30.0
    # US dollars per million tokens, as priced on `priced_on`.
    input_price: Decimal = Decimal(0)
    output_price: Decimal = Decimal(0)
    priced_on: str = ""

    def __post_init__(self) -> None:
        if not self.account:
            object.__setattr__(self, "account", self.provider)


@dataclass(frozen=True)
class ProviderAccount:
    """How to reach one provider. Comes from JALADA_MODEL_PROVIDERS, which is secret."""

    api_key: str | None = None
    base_url: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


def load_catalogue(extra_json: str = "", path: Path = CATALOGUE) -> dict[str, ModelProfile]:
    entries = tomllib.loads(path.read_text()).get("model", [])
    if extra_json.strip():
        entries += json.loads(extra_json)
    return {entry["name"]: _profile(entry) for entry in entries}


def load_accounts(providers_json: str) -> dict[str, ProviderAccount]:
    if not providers_json.strip():
        return {}
    raw: dict[str, dict[str, Any]] = json.loads(providers_json)
    return {
        name: ProviderAccount(
            api_key=values.get("api_key"),
            base_url=values.get("base_url"),
            extra={k: v for k, v in values.items() if k not in ("api_key", "base_url")},
        )
        for name, values in raw.items()
    }


def _profile(entry: dict[str, Any]) -> ModelProfile:
    values = dict(entry)
    for price in ("input_price", "output_price"):
        if price in values:
            values[price] = Decimal(str(values[price]))
    return ModelProfile(**values)
