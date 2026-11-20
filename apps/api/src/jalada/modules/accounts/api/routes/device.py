from fastapi import APIRouter, Request, status

from jalada.dependencies import CurrentUser, ServicesDependency
from jalada.modules.accounts.api.schemas.auth import UserResponse
from jalada.modules.accounts.api.schemas.device import (
    DeviceCodeRequest,
    DeviceCodeResponse,
    DeviceTokenRequest,
    DeviceTokenResponse,
)
from jalada.shared.http.errors import TooManyAttempts

router = APIRouter(tags=["auth"])


@router.post("/v1/auth/device/codes", status_code=status.HTTP_201_CREATED)
def issue_device_code(
    body: DeviceCodeRequest, user: CurrentUser, services: ServicesDependency
) -> DeviceCodeResponse:
    """Called by the web app once the signed-in person agrees to sign the desktop app in."""
    issued = services.device_sign_in.issue_code(user.id, body.challenge)
    return DeviceCodeResponse(code=issued.code, expires_at=issued.expires_at)


@router.post("/v1/auth/device/token")
def exchange_device_code(
    body: DeviceTokenRequest, request: Request, services: ServicesDependency
) -> DeviceTokenResponse:
    """Called by the desktop app with the code from the browser and its own verifier."""
    client = request.client.host if request.client else "unknown"
    if not services.sign_in_limiter.allow(f"ip:{client}", "device"):
        raise TooManyAttempts
    issued = services.device_sign_in.exchange(body.code, body.verifier)
    return DeviceTokenResponse(
        token=issued.token,
        expires_at=issued.expires_at,
        user=UserResponse.from_user(issued.user),
    )
