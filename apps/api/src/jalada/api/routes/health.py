from typing import Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ok"]
    version: str


@router.get("/health")
def read_health(request: Request) -> HealthResponse:
    """Tell the host the process is up. Cheap on purpose: it runs every few seconds."""
    return HealthResponse(status="ok", version=request.app.state.settings.version)
