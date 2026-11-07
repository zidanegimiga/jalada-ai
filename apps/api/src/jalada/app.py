from collections.abc import Callable
from contextlib import AbstractAsyncContextManager

from fastapi import FastAPI

from jalada.core.settings import Settings
from jalada.modules.accounts import module as accounts
from jalada.modules.evidence import module as evidence
from jalada.modules.exports import module as exports
from jalada.modules.health import module as health
from jalada.modules.ledger import module as ledger
from jalada.modules.telegram import module as telegram
from jalada.services import Services
from jalada.shared.http.errors import add_error_handlers
from jalada.shared.http.request_context import RequestContext

Lifespan = Callable[[FastAPI], AbstractAsyncContextManager[None]]

# Every module the app is built from. A new feature adds its module here.
MODULES = [health, accounts, evidence, ledger, exports, telegram]


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
    for module in MODULES:
        for router in module.ROUTERS:
            app.include_router(router)
    return app
