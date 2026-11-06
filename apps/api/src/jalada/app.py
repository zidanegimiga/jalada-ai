from collections.abc import Callable
from contextlib import AbstractAsyncContextManager

from fastapi import FastAPI

from jalada.core.settings import Settings
from jalada.modules.accounts.api.routes import account, auth, google
from jalada.modules.evidence.api.routes import evidence
from jalada.modules.exports.api.routes import exports
from jalada.modules.health.api.routes import health
from jalada.modules.ledger.api.routes import certificates, ledger, review
from jalada.modules.telegram.api.routes import telegram
from jalada.services import Services
from jalada.shared.http.errors import add_error_handlers
from jalada.shared.http.request_context import RequestContext

Lifespan = Callable[[FastAPI], AbstractAsyncContextManager[None]]


def create_app(settings: Settings, services: Services, lifespan: Lifespan | None = None) -> FastAPI:
    """Build the HTTP app. Everything it needs is passed in; nothing is imported globally."""
    show_docs = settings.environment != "production"
    app = FastAPI(
        title="Jalada AI",
        docs_url="/docs" if show_docs else None,
        redoc_url=None,
        openapi_url="/openapi.json" if show_docs else None,
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.services = services
    add_error_handlers(app)
    app.add_middleware(RequestContext)
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(google.router)
    app.include_router(evidence.router)
    app.include_router(review.router)
    app.include_router(ledger.router)
    app.include_router(certificates.router)
    app.include_router(exports.router)
    app.include_router(telegram.router)
    app.include_router(account.router)
    return app
