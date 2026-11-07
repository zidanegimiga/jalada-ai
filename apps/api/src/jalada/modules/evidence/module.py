"""What the evidence module adds to the app."""

from fastapi import APIRouter

from jalada.modules.evidence.api.routes import evidence

ROUTERS: list[APIRouter] = [evidence.router]
