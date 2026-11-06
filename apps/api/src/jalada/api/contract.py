"""The API's OpenAPI document, kept in the repository as apps/api/openapi.json.

A test compares the two, so a change to what the API accepts or returns is always a
deliberate one. After changing the API on purpose, run `make openapi` to update the file.

jalada-openapi [path]
"""

import json
import sys
from pathlib import Path
from typing import Any, cast

from pydantic import SecretStr

from jalada.api.app import create_app
from jalada.api.services import Services
from jalada.config.settings import Settings

CONTRACT = Path(__file__).resolve().parents[3] / "openapi.json"


def openapi_document() -> dict[str, Any]:
    """Built from the routes alone: nothing is connected and no settings are read."""
    settings = Settings(
        environment="development",
        database_url="postgresql+psycopg://contract@localhost/contract",
        storage_access_key="contract",
        storage_secret_key=SecretStr("contract"),
        evidence_keys=SecretStr("contract"),
    )
    return create_app(settings, cast(Services, None)).openapi()


def as_text(document: dict[str, Any]) -> str:
    return json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else CONTRACT
    path.write_text(as_text(openapi_document()))
    print(f"Wrote {path}")
