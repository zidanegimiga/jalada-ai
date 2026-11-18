"""Composition root: the one place where settings and adapters are wired together."""

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from functools import partial

from fastapi import FastAPI
from sqlalchemy.orm import sessionmaker

from jalada.app import Lifespan, create_app
from jalada.builders import (
    build_agent_budget,
    build_budget,
    build_evidence_store,
    build_language_model,
    build_s3_client,
    start_error_tracking_from,
)
from jalada.core.clock import SystemClock
from jalada.core.health import QUICK, DatabaseCheck, StorageCheck
from jalada.core.jobs.runner import JobRunner, background_jobs
from jalada.core.logging import configure_logging
from jalada.core.settings import Settings, load_settings
from jalada.modules.accounts.wiring import GoogleClient, build_accounts
from jalada.modules.agent.application.conversations import Conversations
from jalada.modules.agent.application.proposals import ActionProposals
from jalada.modules.agent.wiring import (
    build_confirmations,
    build_conversations,
    build_lookups,
    build_tracer,
)
from jalada.modules.evidence.application.evidence_capture import PROCESS_EVIDENCE_JOB
from jalada.modules.evidence.wiring import build_evidence
from jalada.modules.exports.wiring import build_tax_year_export
from jalada.modules.ledger.application.money_accounts import open_default_accounts
from jalada.modules.ledger.wiring import LedgerServices, build_ledger
from jalada.modules.pipeline.wiring import build_evidence_processor
from jalada.modules.telegram.adapters.telegram_bot import TelegramBot
from jalada.modules.telegram.wiring import (
    build_telegram_bot,
    build_telegram_capture,
    build_telegram_linking,
    build_telegram_notifier,
)
from jalada.services import Services
from jalada.shared.http.rate_limit import RateLimiter
from jalada.sql_unit_of_work import SqlUnitOfWork, create_database_engine

POLL_INTERVAL_SECONDS = 5.0


def build_services(settings: Settings) -> Services:
    engine = create_database_engine(settings.database_url)
    unit_of_work = partial(SqlUnitOfWork, sessionmaker(engine))
    clock = SystemClock()
    store = build_evidence_store(settings)
    accounts = build_accounts(
        unit_of_work,
        clock,
        store,
        session_days=settings.session_days,
        on_user_created=[open_default_accounts],
        google=google_client(settings),
    )
    ledger = build_ledger(unit_of_work, clock)
    evidence = build_evidence(unit_of_work, store, clock)
    sign_in_limiter = RateLimiter("5/minute")
    upload_limiter = RateLimiter("60/hour")
    telegram_linking = build_telegram_linking(unit_of_work, clock)
    return Services(
        authenticator=accounts.authenticator,
        sign_in_limiter=sign_in_limiter,
        evidence=evidence,
        upload_limiter=upload_limiter,
        review=ledger.review,
        matches=ledger.matches,
        how_paid=ledger.how_paid,
        own_accounts=ledger.own_accounts,
        ledger=ledger.ledger,
        certificate_payments=ledger.certificate_payments,
        tax_year_export=build_tax_year_export(
            unit_of_work, clock, evidence_link=f"{settings.public_url}/v1/evidence/{{id}}/file"
        ),
        telegram_linking=telegram_linking,
        account_export=accounts.account_export,
        account_deletion=accounts.account_deletion,
        google_sign_in=accounts.google_sign_in,
        telegram_capture=build_telegram_capture(
            telegram_bot(settings), telegram_linking, evidence, sign_in_limiter, upload_limiter
        ),
        conversations=assistant(settings, unit_of_work, clock, ledger),
        assistant_actions=(
            build_confirmations(unit_of_work, clock, ledger.review)
            if settings.agent_enabled
            else None
        ),
        assistant_limiter=RateLimiter(f"{settings.agent_questions_per_hour}/hour"),
        health_checks=[
            DatabaseCheck(engine),
            StorageCheck(build_s3_client(settings, QUICK), settings.storage_bucket),
        ],
    )


def assistant(
    settings: Settings,
    unit_of_work: Callable[[], SqlUnitOfWork],
    clock: SystemClock,
    ledger: LedgerServices,
) -> Conversations | None:
    if not settings.agent_enabled:
        return None
    return build_conversations(
        unit_of_work,
        clock,
        build_language_model(settings),
        build_agent_budget(settings),
        settings.database_url,
        build_lookups(
            ledger.ledger,
            ledger.review,
            settings.public_url,
            ActionProposals(unit_of_work, clock),
        ),
        build_tracer(
            settings.agent_traces_url,
            headers.get_secret_value() if (headers := settings.agent_traces_headers) else None,
            settings.version,
        ),
    )


def google_client(settings: Settings) -> GoogleClient | None:
    if not (settings.google_client_id and settings.google_client_secret):
        return None
    return GoogleClient(
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret.get_secret_value(),
        redirect_uri=f"{settings.public_url}/v1/auth/google/callback",
    )


def telegram_bot(settings: Settings) -> TelegramBot | None:
    token = settings.telegram_bot_token
    return build_telegram_bot(
        token.get_secret_value() if token else None, settings.telegram_bot_username
    )


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

    def unit_of_work() -> SqlUnitOfWork:
        return SqlUnitOfWork(session_factory)

    clock = SystemClock()
    processor = build_evidence_processor(
        unit_of_work,
        store=build_evidence_store(settings),
        clock=clock,
        budget=build_budget(settings),
        model=build_language_model(settings),
        notifier=build_telegram_notifier(
            unit_of_work, telegram_bot(settings), f"{settings.public_url}/review"
        ),
    )
    return JobRunner(unit_of_work, {PROCESS_EVIDENCE_JOB: processor}, clock)
