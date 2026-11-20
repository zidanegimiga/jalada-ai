import uuid
from collections.abc import Callable
from datetime import timedelta

import pytest
from fakes import (
    FakeChat,
    FakeEvidenceStore,
    FakeGoogle,
    FakeHasher,
    FakeTextReader,
    FakeUnitOfWork,
    FixedClock,
    ScriptedModel,
    Store,
)
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr
from receipts import LEISURE, RECEIPT, USER, Send
from samples import JPEG, MPESA_PAYBILL
from transfers import Paste

from jalada.app import create_app
from jalada.core.ports import HealthCheck
from jalada.core.settings import Environment, Settings
from jalada.modules.accounts.adapters.account_archive import ZipAccountArchive
from jalada.modules.accounts.application.account_deletion import AccountDeletion
from jalada.modules.accounts.application.account_export import AccountExport
from jalada.modules.accounts.application.authentication import Authenticator
from jalada.modules.accounts.application.device_sign_in import DeviceSignIn
from jalada.modules.accounts.application.google_sign_in import GoogleSignIn
from jalada.modules.accounts.application.model_consent import ConsentToModels
from jalada.modules.agent.application.confirmations import ActionConfirmations
from jalada.modules.agent.application.conversations import Conversations
from jalada.modules.evidence.application.evidence_capture import EvidenceCapture
from jalada.modules.evidence.domain.evidence import EvidenceSource
from jalada.modules.exports.adapters.workbook import ExcelWorkbookWriter
from jalada.modules.exports.application.tax_year_export import TaxYearExport
from jalada.modules.ledger.application.certificate_payments import CertificatePayments
from jalada.modules.ledger.application.entry_review import EntryReview
from jalada.modules.ledger.application.how_paid import HowPaid
from jalada.modules.ledger.application.ledger import Ledger
from jalada.modules.ledger.application.match_review import MatchReview
from jalada.modules.ledger.application.money_accounts import open_default_accounts
from jalada.modules.ledger.application.own_accounts import OwnAccounts
from jalada.modules.pipeline.application.evidence_processing import EvidenceProcessor
from jalada.modules.pipeline.domain.run_types import Budget
from jalada.modules.telegram.application.telegram_capture import TelegramCapture
from jalada.modules.telegram.application.telegram_linking import TelegramLinking
from jalada.services import Services
from jalada.shared.http.rate_limit import RateLimiter

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
    return Authenticator(
        lambda: FakeUnitOfWork(store),
        hasher,
        clock,
        timedelta(days=30),
        on_user_created=[open_default_accounts],
    )


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
    evidence_store: FakeEvidenceStore,
) -> Callable[..., FastAPI]:
    def build(
        environment: Environment = "test",
        rule: str = "100/minute",
        with_google: bool = True,
        upload_rule: str = "100/minute",
        with_telegram: bool = True,
        health_checks: list[HealthCheck] | None = None,
        assistant: Conversations | None = None,
        assistant_rule: str = "100/minute",
        assistant_actions: ActionConfirmations | None = None,
        consent_notice: str | None = None,
    ) -> FastAPI:
        services = Services(
            authenticator=authenticator,
            sign_in_limiter=RateLimiter(rule),
            evidence=capture,
            upload_limiter=RateLimiter(upload_rule),
            review=review,
            matches=MatchReview(lambda: FakeUnitOfWork(store), FixedClock()),
            how_paid=HowPaid(lambda: FakeUnitOfWork(store), FixedClock()),
            own_accounts=OwnAccounts(lambda: FakeUnitOfWork(store), FixedClock()),
            ledger=Ledger(lambda: FakeUnitOfWork(store)),
            certificate_payments=CertificatePayments(lambda: FakeUnitOfWork(store), FixedClock()),
            tax_year_export=TaxYearExport(
                lambda: FakeUnitOfWork(store),
                ExcelWorkbookWriter(),
                FixedClock(),
                "http://localhost:3000/v1/evidence/{id}/file",
            ),
            telegram_linking=linking,
            account_export=AccountExport(
                lambda: FakeUnitOfWork(store), evidence_store, ZipAccountArchive()
            ),
            account_deletion=AccountDeletion(lambda: FakeUnitOfWork(store), evidence_store),
            model_consent=ConsentToModels(
                lambda: FakeUnitOfWork(store), FixedClock(), consent_notice
            ),
            device_sign_in=DeviceSignIn(
                lambda: FakeUnitOfWork(store), FixedClock(), timedelta(days=30)
            ),
            telegram_capture=telegram if with_telegram else None,
            google_sign_in=GoogleSignIn(google, authenticator) if with_google else None,
            health_checks=health_checks or [],
            conversations=assistant,
            assistant_limiter=RateLimiter(assistant_rule),
            assistant_actions=assistant_actions,
        )
        return create_app(make_settings(environment), services)

    return build


@pytest.fixture
def client(make_app: Callable[..., FastAPI]) -> TestClient:
    return TestClient(make_app())


@pytest.fixture
def send(  # see receipts.Send
    store: Store, capture: EvidenceCapture, evidence_store: FakeEvidenceStore, clock: FixedClock
) -> Send:
    def sent(
        what: str, receipt: dict[str, object] = RECEIPT, user: uuid.UUID = USER
    ) -> tuple[uuid.UUID, str]:
        if what == "receipt":
            photo = JPEG + uuid.uuid4().bytes
            evidence = capture.capture_file(user, photo, EvidenceSource.WEB_UPLOAD).evidence
        else:
            evidence = capture.capture_text(user, MPESA_PAYBILL, EvidenceSource.WEB_PASTE).evidence
        processor = EvidenceProcessor(
            lambda: FakeUnitOfWork(store),
            evidence_store,
            FakeTextReader(),
            clock,
            Budget(),
            model=ScriptedModel(receipt, LEISURE),
        )
        return evidence.id, processor.process(user, evidence.id)

    return sent


@pytest.fixture
def paste(  # see transfers.Paste
    store: Store, capture: EvidenceCapture, evidence_store: FakeEvidenceStore, clock: FixedClock
) -> Paste:
    def pasted(message: str, user: uuid.UUID = USER) -> uuid.UUID:
        evidence = capture.capture_text(user, message, EvidenceSource.WEB_PASTE).evidence
        processor = EvidenceProcessor(
            lambda: FakeUnitOfWork(store), evidence_store, FakeTextReader(), clock, Budget()
        )
        processor.process(user, evidence.id)
        [payment] = [
            t for t in store.transactions.values() if t.evidence[0].evidence_id == evidence.id
        ]
        return payment.id

    return pasted
