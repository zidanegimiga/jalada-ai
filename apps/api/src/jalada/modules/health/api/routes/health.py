from typing import Literal

from fastapi import APIRouter, Request, Response, status
from pydantic import BaseModel

from jalada.dependencies import ServicesDependency

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ok"]
    version: str


class ReadinessResponse(BaseModel):
    status: Literal["ok", "failing"]
    version: str
    checks: dict[str, Literal["ok", "failing"]]


@router.get("/health")
def read_health(request: Request) -> HealthResponse:
    """Tell the host the process is up. Cheap on purpose: it runs every few seconds."""
    return HealthResponse(status="ok", version=request.app.state.settings.version)


@router.get("/health/ready")
def read_readiness(
    request: Request, response: Response, services: ServicesDependency
) -> ReadinessResponse:
    """Whether the API can reach the database and evidence storage. 503 if either fails."""
    checks: dict[str, Literal["ok", "failing"]] = {
        check.name: "ok" if check.ok() else "failing" for check in services.health_checks
    }
    ready = all(result == "ok" for result in checks.values())
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(
        status="ok" if ready else "failing",
        version=request.app.state.settings.version,
        checks=checks,
    )
