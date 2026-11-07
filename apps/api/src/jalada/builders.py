"""Adapters built from settings alone: storage, the language model and error tracking."""

from typing import TYPE_CHECKING

from jalada.core.error_tracking import start_error_tracking
from jalada.core.settings import Settings
from jalada.core.storage.client import create_s3_client
from jalada.modules.evidence.adapters.cipher import EvidenceCipher
from jalada.modules.evidence.adapters.storage import EncryptedS3EvidenceStore
from jalada.modules.evidence.application.ports import EvidenceStore
from jalada.modules.pipeline.adapters.models.chain import ChainLink, ModelChain
from jalada.modules.pipeline.adapters.models.profiles import load_accounts, load_catalogue
from jalada.modules.pipeline.adapters.models.registry import ModelSetupError, build_model
from jalada.modules.pipeline.domain.model import LanguageModel
from jalada.modules.pipeline.domain.run_types import Budget

if TYPE_CHECKING:
    from botocore.config import Config
    from mypy_boto3_s3 import S3Client


def start_error_tracking_from(settings: Settings) -> bool:
    """Sentry, when JALADA_SENTRY_DSN is set. True if errors will be sent."""
    dsn = settings.sentry_dsn.get_secret_value() if settings.sentry_dsn else None
    return start_error_tracking(dsn, settings.environment, settings.version)


def build_s3_client(settings: Settings, config: "Config | None" = None) -> "S3Client":
    return create_s3_client(
        endpoint_url=settings.storage_endpoint_url,
        region=settings.storage_region,
        access_key=settings.storage_access_key,
        secret_key=settings.storage_secret_key.get_secret_value(),
        config=config,
    )


def build_evidence_store(settings: Settings) -> EvidenceStore:
    keys = settings.evidence_keys.get_secret_value().split(",")
    ciphers = [EvidenceCipher.from_base64(key.strip()) for key in keys]
    return EncryptedS3EvidenceStore(build_s3_client(settings), settings.storage_bucket, ciphers)


def build_language_model(settings: Settings) -> LanguageModel | None:
    """The models named in JALADA_MODEL_CHAIN, as one chain that falls back in order.

    None when no model is named. Any setting that cannot work stops startup with a
    ModelSetupError saying which one.
    """
    names = settings.model_chain_names
    if not names:
        return None
    try:
        catalogue = load_catalogue(settings.extra_models)
        secret = settings.model_providers.get_secret_value() if settings.model_providers else ""
        accounts = load_accounts(secret)
    except (ValueError, TypeError) as error:
        # The message names the problem only: the providers setting holds API keys.
        raise ModelSetupError(
            f"JALADA_MODEL_PROVIDERS or JALADA_EXTRA_MODELS is not valid: {type(error).__name__}"
        ) from None
    links = []
    for name in names:
        profile = catalogue.get(name)
        if profile is None:
            raise ModelSetupError(f"JALADA_MODEL_CHAIN names {name!r}, not in the catalogue")
        links.append(ChainLink(profile, build_model(profile, accounts)))
    return ModelChain(links)


def build_budget(settings: Settings) -> Budget:
    return Budget(
        max_attempts=settings.pipeline_max_attempts,
        max_tokens=settings.pipeline_max_tokens,
        max_cost_usd=settings.pipeline_max_cost_usd,
    )
