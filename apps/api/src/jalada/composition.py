"""Composition root: the one place where settings and adapters are wired together.

Start the API with:
    uvicorn jalada.composition:build_api --factory
"""

from fastapi import FastAPI

from jalada.api.app import create_app
from jalada.config.settings import load_settings


def build_api() -> FastAPI:
    settings = load_settings()
    return create_app(settings)
