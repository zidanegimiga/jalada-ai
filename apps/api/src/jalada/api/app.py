from fastapi import FastAPI

from jalada.api.routes import health
from jalada.config.settings import Settings


def create_app(settings: Settings) -> FastAPI:
    """Build the HTTP app. Everything it needs is passed in; nothing is imported globally."""
    show_docs = settings.environment != "production"
    app = FastAPI(
        title="Jalada AI",
        docs_url="/docs" if show_docs else None,
        redoc_url=None,
        openapi_url="/openapi.json" if show_docs else None,
    )
    app.include_router(health.router)
    return app
