from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ok"]


@router.get("/health")
def read_health() -> HealthResponse:
    """Tell load balancers and docker compose that the process is up."""
    return HealthResponse(status="ok")
