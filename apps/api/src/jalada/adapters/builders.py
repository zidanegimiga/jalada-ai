"""Adapters built from settings alone: evidence storage and the language model."""

from typing import TYPE_CHECKING

from jalada.adapters.models.gemini import GeminiModel
from jalada.adapters.models.ollama import OllamaModel
from jalada.adapters.models.pricing import Pricing
from jalada.adapters.security.evidence_cipher import EvidenceCipher
from jalada.adapters.storage.s3_store import EncryptedS3EvidenceStore, create_s3_client
from jalada.application.ports import EvidenceStore
from jalada.config.settings import Settings
from jalada.pipeline.model import LanguageModel
from jalada.pipeline.run_types import Budget

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client


def build_s3_client(settings: Settings) -> "S3Client":
    return create_s3_client(
        endpoint_url=settings.storage_endpoint_url,
        region=settings.storage_region,
        access_key=settings.storage_access_key,
        secret_key=settings.storage_secret_key.get_secret_value(),
    )


def build_evidence_store(settings: Settings) -> EvidenceStore:
    keys = settings.evidence_keys.get_secret_value().split(",")
    ciphers = [EvidenceCipher.from_base64(key.strip()) for key in keys]
    return EncryptedS3EvidenceStore(build_s3_client(settings), settings.storage_bucket, ciphers)


def build_language_model(settings: Settings) -> LanguageModel | None:
    name = settings.resolved_model_name
    if settings.model_provider == "gemini" and settings.gemini_api_key:
        pricing = Pricing(settings.model_input_price, settings.model_output_price)
        return GeminiModel(settings.gemini_api_key.get_secret_value(), name, pricing)
    if settings.model_provider == "ollama":
        return OllamaModel(settings.ollama_url, name)
    return None


def build_budget(settings: Settings) -> Budget:
    return Budget(
        max_attempts=settings.pipeline_max_attempts,
        max_tokens=settings.pipeline_max_tokens,
        max_cost_usd=settings.pipeline_max_cost_usd,
    )
