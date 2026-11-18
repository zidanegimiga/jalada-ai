"""What the agent module adds to the app."""

from fastapi import APIRouter

# The chat routes come with server-sent events; until then the assistant has no routes.
ROUTERS: list[APIRouter] = []
