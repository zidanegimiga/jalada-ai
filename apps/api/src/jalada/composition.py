"""Composition root: the one place where settings and adapters are wired together."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import timedelta
from functools import partial

from fastapi import FastAPI
from sqlalchemy.orm import sessionmaker

from jalada.adapters.builders import (
    build_budget,
    build_evidence_store,
    build_language_model,
    build_s3_client,
    start_error_tracking_from,
)
from jalada.adapters.channels.telegram_bot import TelegramBot
from jalada.adapters.database.unit_of_work import SqlUnitOfWork, create_database_engine
from jalada.adapters.export.account_archive import ZipAccountArchive
from jalada.adapters.export.workbook import ExcelWorkbookWriter
from jalada.adapters.health import QUICK, DatabaseCheck, StorageCheck
from jalada.adapters.identity.google import GoogleOpenIdClient
from jalada.adapters.security.argon2_hasher import Argon2PasswordHasher
from jalada.adapters.system_clock import SystemClock
from jalada.adapters.text.ocr import TesseractOcr
from jalada.adapters.text.reader import EvidenceTextReader
from jalada.api.app import Lifespan, create_app
from jalada.api.rate_limit import RateLimiter
from jalada.api.services import Services
from jalada.application.account_deletion import AccountDeletion
from jalada.application.account_export import AccountExport
from jalada.application.authentication import Authenticator
from jalada.application.certificate_payments import CertificatePayments
from jalada.application.entry_review import EntryReview
from jalada.application.evidence_capture import PROCESS_EVIDENCE_JOB, EvidenceCapture
from jalada.application.evidence_processing import EvidenceProcessor
from jalada.application.google_sign_in import GoogleSignIn
from jalada.application.job_runner import JobRunner, background_jobs
from jalada.application.ledger import Ledger
from jalada.application.tax_year_export import TaxYearExport
from jalada.application.telegram_capture import TelegramCapture
from jalada.application.telegram_linking import TelegramLinking
from jalada.application.telegram_notifier import TelegramNotifier
from jalada.config.logging import configure_logging
from jalada.config.settings import Settings, load_settings

POLL_INTERVAL_SECONDS = 5.0


def build_services(settings: Settings) -> Services:
    engine = create_database_engine(settings.database_url)
    unit_of_work = partial(SqlUnitOfWork, sessionmaker(engine))
    clock = SystemClock()
    store = build_evidence_store(settings)
    authenticator = Authenticator(
        unit_of_work=unit_of_work,
        hasher=Argon2PasswordHasher(),
        clock=clock,
        session_lifetime=timedelta(days=settings.session_days),
    )
    evidence = EvidenceCapture(unit_of_work=unit_of_work, store=store, clock=clock)
    sign_in_limiter = RateLimiter("5/minute")
    upload_limiter = RateLimiter("60/hour")
    telegram_linking = TelegramLinking(unit_of_work, clock)
    return Services(
        authenticator=authenticator,
        sign_in_limiter=sign_in_limiter,
        evidence=evidence,
        upload_limiter=upload_limiter,
        review=EntryReview(unit_of_work, clock),
        ledger=Ledger(unit_of_work),
        certificate_payments=CertificatePayments(unit_of_work, clock),
        tax_year_export=TaxYearExport(
            unit_of_work,
            ExcelWorkbookWriter(),
            clock,
            evidence_link=f"{settings.public_url}/v1/evidence/{{id}}/file",
        ),
        telegram_linking=telegram_linking,
        account_export=AccountExport(unit_of_work, store, ZipAccountArchive()),
        account_deletion=AccountDeletion(unit_of_work, store),
        google_sign_in=build_google_sign_in(settings, authenticator),
        telegram_capture=build_telegram_capture(
            settings, telegram_linking, evidence, sign_in_limiter, upload_limiter
        ),
        health_checks=[
            DatabaseCheck(engine),
            StorageCheck(build_s3_client(settings, QUICK), settings.storage_bucket),
        ],
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


def build_google_sign_in(settings: Settings, authenticator: Authenticator) -> GoogleSignIn | None:
    if not (settings.google_client_id and settings.google_client_secret):
        return None
    google = GoogleOpenIdClient(
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret.get_secret_value(),
        redirect_uri=f"{settings.public_url}/v1/auth/google/callback",
    )
    return GoogleSignIn(google, authenticator)


def build_api() -> FastAPI:
    settings = load_settings()
    configure_logging(settings.log_level, settings.json_logs)
    start_error_tracking_from(settings)
    lifespan = jobs_in_background(settings) if settings.run_worker_in_api else None
    return create_app(settings, build_services(settings), lifespan)


def jobs_in_background(settings: Settings) -> Lifespan:
    """Runs the worker's job loop on a thread inside the API, for free hosts."""
    runner = build_job_runner(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        with background_jobs(runner, POLL_INTERVAL_SECONDS):
            yield

    return lifespan


def build_job_runner(settings: Settings) -> JobRunner:
    """The worker's job loop: the pipeline, with replies on Telegram when the bot is on."""
    session_factory = sessionmaker(create_database_engine(settings.database_url))
    clock = SystemClock()
    bot = build_telegram_bot(settings)
    notifier = (
        TelegramNotifier(
            lambda: SqlUnitOfWork(session_factory), bot, f"{settings.public_url}/review"
        )
        if bot
        else None
    )
    processor = EvidenceProcessor(
        unit_of_work=lambda: SqlUnitOfWork(session_factory),
        store=build_evidence_store(settings),
        reader=EvidenceTextReader(TesseractOcr()),
        clock=clock,
        budget=build_budget(settings),
        model=build_language_model(settings),
        notifier=notifier,
    )
    return JobRunner(
        lambda: SqlUnitOfWork(session_factory), {PROCESS_EVIDENCE_JOB: processor}, clock
    )
