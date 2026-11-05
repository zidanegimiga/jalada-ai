"""Start the API the way a host runs it: optional migrations first, then the web server.

jalada-serve
"""

import os

import uvicorn

from jalada.adapters.database.migrate import upgrade
from jalada.adapters.storage.setup import ensure_bucket
from jalada.config.logging import configure_logging
from jalada.config.settings import load_settings


def main() -> None:
    settings = load_settings()
    configure_logging(settings.log_level)
    if settings.migrate_on_start:
        upgrade(settings.database_url)
        ensure_bucket(settings)
    uvicorn.run(
        "jalada.composition:build_api",
        factory=True,
        # Inside a container the server must listen on every interface.
        host="0.0.0.0",  # noqa: S104
        # Hosts such as Render say which port to use through PORT.
        port=int(os.environ.get("PORT", "8000")),
        # Requests arrive through the web app's proxy and the host's load balancer. Reading
        # X-Forwarded-For gives each visitor's own address, which the rate limits count by.
        proxy_headers=True,
        forwarded_allow_ips="*",
        log_level=settings.log_level.lower(),
    )
