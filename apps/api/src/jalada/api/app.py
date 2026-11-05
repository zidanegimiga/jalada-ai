from fastapi import FastAPI

from jalada.api.errors import add_error_handlers
from jalada.api.routes import (
    account,
    auth,
    evidence,
    exports,
    google,
    health,
    ledger,
    review,
    telegram,
)
from jalada.api.services import Services
from jalada.config.settings import Settings


def create_app(settings: Settings, services: Services) -> FastAPI:
    """Build the HTTP app. Everything it needs is passed in; nothing is imported globally."""
    show_docs = settings.environment != "production"
    app = FastAPI(
        title="Jalada AI",
        docs_url="/docs" if show_docs else None,
        redoc_url=None,
        openapi_url="/openapi.json" if show_docs else None,
    )
    app.state.settings = settings
    app.state.services = services
    add_error_handlers(app)
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(google.router)
    app.include_router(evidence.router)
    app.include_router(review.router)
    app.include_router(ledger.router)
    app.include_router(exports.router)
    app.include_router(telegram.router)
    app.include_router(account.router)
    return app
