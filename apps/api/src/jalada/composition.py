"""Composition root: the one place where settings and adapters are wired together.

Start the API with:
    uvicorn jalada.composition:build_api --factory
"""

from datetime import timedelta

from fastapi import FastAPI
from sqlalchemy.orm import sessionmaker

from jalada.adapters.channels.telegram_bot import TelegramBot
from jalada.adapters.database.unit_of_work import SqlUnitOfWork, create_database_engine
from jalada.adapters.export.account_archive import ZipAccountArchive
from jalada.adapters.export.workbook import ExcelWorkbookWriter
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
from jalada.application.account_export import AccountExport
from jalada.application.authentication import Authenticator
from jalada.application.entry_review import EntryReview
from jalada.application.evidence_capture import EvidenceCapture
from jalada.application.google_sign_in import GoogleSignIn
from jalada.application.ledger import Ledger
from jalada.application.ports import EvidenceStore
from jalada.application.tax_year_export import TaxYearExport
from jalada.application.telegram_capture import TelegramCapture
from jalada.application.telegram_linking import TelegramLinking
from jalada.config.logging import configure_logging
from jalada.config.settings import Settings, load_settings
from jalada.pipeline.model import LanguageModel
from jalada.pipeline.run_types import Budget


def build_services(settings: Settings) -> Services:
    session_factory = sessionmaker(create_database_engine(settings.database_url))
    clock = SystemClock()
    store = build_evidence_store(settings)
    authenticator = Authenticator(
        unit_of_work=lambda: SqlUnitOfWork(session_factory),
        hasher=Argon2PasswordHasher(),
        clock=clock,
        session_lifetime=timedelta(days=settings.session_days),
    )
    evidence = EvidenceCapture(
        unit_of_work=lambda: SqlUnitOfWork(session_factory),
        store=store,
        clock=clock,
    )
    sign_in_limiter = RateLimiter("5/minute")
    upload_limiter = RateLimiter("60/hour")
    telegram_linking = TelegramLinking(lambda: SqlUnitOfWork(session_factory), clock)
    return Services(
        authenticator=authenticator,
        sign_in_limiter=sign_in_limiter,
        evidence=evidence,
        upload_limiter=upload_limiter,
        review=EntryReview(lambda: SqlUnitOfWork(session_factory), clock),
        ledger=Ledger(lambda: SqlUnitOfWork(session_factory)),
        tax_year_export=TaxYearExport(
            lambda: SqlUnitOfWork(session_factory),
            ExcelWorkbookWriter(),
            clock,
            evidence_link=f"{settings.public_url}/v1/evidence/{{id}}/file",
        ),
        telegram_linking=telegram_linking,
        account_export=AccountExport(
            lambda: SqlUnitOfWork(session_factory), store, ZipAccountArchive()
        ),
        google_sign_in=build_google_sign_in(settings, authenticator),
        telegram_capture=build_telegram_capture(
            settings, telegram_linking, evidence, sign_in_limiter, upload_limiter
        ),
    )


def build_telegram_capture(
    settings: Settings,
    linking: TelegramLinking,
    evidence: EvidenceCapture,
    link_limiter: RateLimiter,
    upload_limiter: RateLimiter,
) -> TelegramCapture | None:
    bot = build_telegram_bot(settings)
    if bot is None:
        return None
    return TelegramCapture(linking, evidence, bot, link_limiter, upload_limiter)


def build_telegram_bot(settings: Settings) -> TelegramBot | None:
    """The bot, when both its token and its username are set."""
    if not (settings.telegram_bot_token and settings.telegram_bot_username):
        return None
    return TelegramBot(settings.telegram_bot_token.get_secret_value())


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
    configure_logging(settings.log_level)
    return create_app(settings, build_services(settings))
