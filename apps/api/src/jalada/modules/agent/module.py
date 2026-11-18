"""What the agent module adds to the app."""

from fastapi import APIRouter

from jalada.modules.agent.api.routes import assistant

ROUTERS: list[APIRouter] = [assistant.router]
