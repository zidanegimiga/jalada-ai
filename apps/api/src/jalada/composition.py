"""Composition root: the one place where settings and adapters are wired together.

Start the API with:
    uvicorn jalada.composition:build_api --factory
"""

from datetime import timedelta

from fastapi import FastAPI
from sqlalchemy.orm import sessionmaker

from jalada.adapters.database.unit_of_work import SqlUnitOfWork, create_database_engine
from jalada.adapters.identity.google import GoogleOpenIdClient
from jalada.adapters.security.argon2_hasher import Argon2PasswordHasher
from jalada.adapters.system_clock import SystemClock
from jalada.api.app import create_app
from jalada.api.rate_limit import RateLimiter
from jalada.api.services import Services
from jalada.application.authentication import Authenticator
from jalada.application.google_sign_in import GoogleSignIn
from jalada.config.settings import Settings, load_settings


def build_services(settings: Settings) -> Services:
    session_factory = sessionmaker(create_database_engine(settings.database_url))
    authenticator = Authenticator(
        unit_of_work=lambda: SqlUnitOfWork(session_factory),
        hasher=Argon2PasswordHasher(),
        clock=SystemClock(),
        session_lifetime=timedelta(days=settings.session_days),
    )
    return Services(
        authenticator=authenticator,
        sign_in_limiter=RateLimiter("5/minute"),
        google_sign_in=build_google_sign_in(settings, authenticator),
    )


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
    return create_app(settings, build_services(settings))
