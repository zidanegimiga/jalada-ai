from typing import Annotated

from fastapi import APIRouter, Cookie, Request, Response, status

from jalada.api.dependencies import SESSION_COOKIE, CurrentUser, ServicesDependency
from jalada.api.errors import TooManyAttempts
from jalada.api.schemas.auth import SignInRequest, SignUpRequest, UserResponse
from jalada.application.authentication import IssuedSession

router = APIRouter(tags=["auth"])


def _set_session_cookie(request: Request, response: Response, issued: IssuedSession) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        issued.token,
        expires=issued.expires_at,
        httponly=True,
        secure=request.app.state.settings.cookie_secure,
        samesite="lax",
    )


def _check_rate(request: Request, services: ServicesDependency, email: str) -> None:
    client = request.client.host if request.client else "unknown"
    if not services.sign_in_limiter.allow(f"ip:{client}", f"email:{email.lower()}"):
        raise TooManyAttempts


@router.post("/v1/auth/signup", status_code=status.HTTP_201_CREATED)
def sign_up(
    body: SignUpRequest, request: Request, response: Response, services: ServicesDependency
) -> UserResponse:
    _check_rate(request, services, body.email)
    issued = services.authenticator.sign_up(body.email, body.password, body.display_name)
    _set_session_cookie(request, response, issued)
    return UserResponse.from_user(issued.user)


@router.post("/v1/auth/login")
def sign_in(
    body: SignInRequest, request: Request, response: Response, services: ServicesDependency
) -> UserResponse:
    _check_rate(request, services, body.email)
    issued = services.authenticator.sign_in(body.email, body.password)
    _set_session_cookie(request, response, issued)
    return UserResponse.from_user(issued.user)


@router.post("/v1/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def sign_out(
    response: Response,
    services: ServicesDependency,
    session_token: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
) -> None:
    if session_token:
        services.authenticator.sign_out(session_token)
    response.delete_cookie(SESSION_COOKIE)


@router.get("/v1/me")
def read_me(user: CurrentUser) -> UserResponse:
    return UserResponse.from_user(user)
