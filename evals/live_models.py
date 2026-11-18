"""A real model from the catalogue, for evals run against a provider instead of replies.

The key and address come from JALADA_MODEL_PROVIDERS in the environment, never from a file
here. Every eval record is invented, so any model may see it, free tiers included.
"""

import os

from pydantic import SecretStr

from jalada.builders import build_language_model
from jalada.core.settings import Settings
from jalada.modules.pipeline.domain.model import LanguageModel


def real_model(name: str) -> LanguageModel:
    settings = Settings(
        environment="development",
        database_url="postgresql+psycopg://unused@localhost/unused",
        storage_access_key="unused",
        storage_secret_key=SecretStr("unused"),
        evidence_keys=SecretStr("unused"),
        model_chain=name,
        model_providers=SecretStr(os.environ.get("JALADA_MODEL_PROVIDERS", "{}")),
        extra_models=os.environ.get("JALADA_EXTRA_MODELS", ""),
    )
    model = build_language_model(settings)
    if model is None:
        raise SystemExit(f"No model called {name!r}")
    return model
