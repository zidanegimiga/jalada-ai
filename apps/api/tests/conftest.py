from collections.abc import Callable
from datetime import timedelta

import pytest
from fakes import FakeGoogle, FakeHasher, FakeUnitOfWork, FixedClock, Store
from fastapi import FastAPI
from fastapi.testclient import TestClient

from jalada.api.app import create_app
from jalada.api.rate_limit import RateLimiter
from jalada.api.services import Services
from jalada.application.authentication import Authenticator
from jalada.application.google_sign_in import GoogleSignIn
from jalada.config.settings import Environment, Settings

pytest_plugins = ["database_fixtures"]

TEST_DATABASE_URL = "postgresql+psycopg://user:pass@localhost:5432/unused"


def make_settings(environment: Environment = "test") -> Settings:
    return Settings(environment=environment, database_url=TEST_DATABASE_URL, cookie_secure=False)


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
def google() -> FakeGoogle:
    return FakeGoogle()


@pytest.fixture
def make_app(authenticator: Authenticator, google: FakeGoogle) -> Callable[..., FastAPI]:
    def build(
        environment: Environment = "test", rule: str = "100/minute", with_google: bool = True
    ) -> FastAPI:
        services = Services(
            authenticator=authenticator,
            sign_in_limiter=RateLimiter(rule),
            google_sign_in=GoogleSignIn(google, authenticator) if with_google else None,
        )
        return create_app(make_settings(environment), services)

    return build


@pytest.fixture
def client(make_app: Callable[..., FastAPI]) -> TestClient:
    return TestClient(make_app())
