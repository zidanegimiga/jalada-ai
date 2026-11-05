from collections.abc import Callable
from datetime import timedelta

import pytest
from fakes import (
    FakeChat,
    FakeEvidenceStore,
    FakeGoogle,
    FakeHasher,
    FakeUnitOfWork,
    FixedClock,
    Store,
)
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr

from jalada.adapters.export.workbook import ExcelWorkbookWriter
from jalada.api.app import create_app
from jalada.api.rate_limit import RateLimiter
from jalada.api.services import Services
from jalada.application.authentication import Authenticator
from jalada.application.entry_review import EntryReview
from jalada.application.evidence_capture import EvidenceCapture
from jalada.application.google_sign_in import GoogleSignIn
from jalada.application.ledger import Ledger
from jalada.application.tax_year_export import TaxYearExport
from jalada.application.telegram_capture import TelegramCapture
from jalada.application.telegram_linking import TelegramLinking
from jalada.config.settings import Environment, Settings

pytest_plugins = ["database_fixtures"]

TEST_DATABASE_URL = "postgresql+psycopg://user:pass@localhost:5432/unused"


def make_settings(environment: Environment = "test") -> Settings:
    return Settings(
        environment=environment,
        database_url=TEST_DATABASE_URL,
        cookie_secure=False,
        storage_access_key="test",
        storage_secret_key=SecretStr("test"),
        evidence_keys=SecretStr("dGVzdC1rZXktZm9yLWV2aWRlbmNlLTMyLWJ5dGVzISE="),
        telegram_webhook_secret=SecretStr("hook-secret"),
    )


@pytest.fixture
def store() -> Store:
    return Store()


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock()


@pytest.fixture
def hasher() -> FakeHasher:
    return FakeHasher()


@pytest.fixture
def authenticator(store: Store, hasher: FakeHasher, clock: FixedClock) -> Authenticator:
    return Authenticator(lambda: FakeUnitOfWork(store), hasher, clock, timedelta(days=30))


@pytest.fixture
def evidence_store() -> FakeEvidenceStore:
    return FakeEvidenceStore()


@pytest.fixture
def capture(store: Store, evidence_store: FakeEvidenceStore, clock: FixedClock) -> EvidenceCapture:
    return EvidenceCapture(lambda: FakeUnitOfWork(store), evidence_store, clock)


@pytest.fixture
def review(store: Store, clock: FixedClock) -> EntryReview:
    return EntryReview(lambda: FakeUnitOfWork(store), clock)


@pytest.fixture
def chat() -> FakeChat:
    return FakeChat()


@pytest.fixture
def linking(store: Store, clock: FixedClock) -> TelegramLinking:
    return TelegramLinking(lambda: FakeUnitOfWork(store), clock)


@pytest.fixture
def telegram(linking: TelegramLinking, capture: EvidenceCapture, chat: FakeChat) -> TelegramCapture:
    return TelegramCapture(
        linking, capture, chat, RateLimiter("3/minute"), RateLimiter("100/minute")
    )


@pytest.fixture
def google() -> FakeGoogle:
    return FakeGoogle()


@pytest.fixture
def make_app(
    authenticator: Authenticator,
    capture: EvidenceCapture,
    review: EntryReview,
    google: FakeGoogle,
    store: Store,
    linking: TelegramLinking,
    telegram: TelegramCapture,
) -> Callable[..., FastAPI]:
    def build(
        environment: Environment = "test",
        rule: str = "100/minute",
        with_google: bool = True,
        upload_rule: str = "100/minute",
        with_telegram: bool = True,
    ) -> FastAPI:
        services = Services(
            authenticator=authenticator,
            sign_in_limiter=RateLimiter(rule),
            evidence=capture,
            upload_limiter=RateLimiter(upload_rule),
            review=review,
            ledger=Ledger(lambda: FakeUnitOfWork(store)),
            tax_year_export=TaxYearExport(
                lambda: FakeUnitOfWork(store),
                ExcelWorkbookWriter(),
                FixedClock(),
                "http://localhost:3000/v1/evidence/{id}/file",
            ),
            telegram_linking=linking,
            telegram_capture=telegram if with_telegram else None,
            google_sign_in=GoogleSignIn(google, authenticator) if with_google else None,
        )
        return create_app(make_settings(environment), services)

    return build


@pytest.fixture
def client(make_app: Callable[..., FastAPI]) -> TestClient:
    return TestClient(make_app())
