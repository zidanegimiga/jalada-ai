"""What the health module adds to the app."""

from fastapi import APIRouter

from jalada.modules.health.api.routes import health

ROUTERS: list[APIRouter] = [health.router]
