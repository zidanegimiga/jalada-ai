"""Composition root: the one place where settings and adapters are wired together.

Start the API with:
    uvicorn jalada.composition:build_api --factory
"""

from datetime import timedelta

from fastapi import FastAPI
from sqlalchemy.orm import sessionmaker

from jalada.adapters.database.unit_of_work import SqlUnitOfWork, create_database_engine
from jalada.adapters.identity.google import GoogleOpenIdClient
from jalada.adapters.models.gemini import GeminiModel
from jalada.adapters.models.ollama import OllamaModel
from jalada.adapters.models.pricing import Pricing
from jalada.adapters.security.argon2_hasher import Argon2PasswordHasher
from jalada.adapters.security.evidence_cipher import EvidenceCipher
from jalada.adapters.storage.s3_store import EncryptedS3EvidenceStore, create_s3_client
from jalada.adapters.system_clock import SystemClock
from jalada.api.app import create_app
from jalada.api.rate_limit import RateLimiter
from jalada.api.services import Services
from jalada.application.authentication import Authenticator
from jalada.application.evidence_capture import EvidenceCapture
from jalada.application.google_sign_in import GoogleSignIn
from jalada.application.ports import EvidenceStore
from jalada.config.settings import Settings, load_settings
from jalada.pipeline.model import LanguageModel
from jalada.pipeline.run_types import Budget


def build_services(settings: Settings) -> Services:
    session_factory = sessionmaker(create_database_engine(settings.database_url))
    clock = SystemClock()
    authenticator = Authenticator(
        unit_of_work=lambda: SqlUnitOfWork(session_factory),
        hasher=Argon2PasswordHasher(),
        clock=clock,
        session_lifetime=timedelta(days=settings.session_days),
    )
    evidence = EvidenceCapture(
        unit_of_work=lambda: SqlUnitOfWork(session_factory),
        store=build_evidence_store(settings),
        clock=clock,
    )
    return Services(
        authenticator=authenticator,
        sign_in_limiter=RateLimiter("5/minute"),
        evidence=evidence,
        upload_limiter=RateLimiter("60/hour"),
        google_sign_in=build_google_sign_in(settings, authenticator),
    )


def build_evidence_store(settings: Settings) -> EvidenceStore:
    keys = settings.evidence_keys.get_secret_value().split(",")
    client = create_s3_client(
        endpoint_url=settings.storage_endpoint_url,
        region=settings.storage_region,
        access_key=settings.storage_access_key,
        secret_key=settings.storage_secret_key.get_secret_value(),
    )
    ciphers = [EvidenceCipher.from_base64(key.strip()) for key in keys]
    return EncryptedS3EvidenceStore(client, settings.storage_bucket, ciphers)


def build_google_sign_in(settings: Settings, authenticator: Authenticator) -> GoogleSignIn | None:
    if not (settings.google_client_id and settings.google_client_secret):
        return None
    google = GoogleOpenIdClient(
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret.get_secret_value(),
        redirect_uri=f"{settings.public_url}/v1/auth/google/callback",
    )
    return GoogleSignIn(google, authenticator)


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


def build_api() -> FastAPI:
    settings = load_settings()
    return create_app(settings, build_services(settings))
