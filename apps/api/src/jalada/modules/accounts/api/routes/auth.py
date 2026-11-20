from typing import Annotated

from fastapi import APIRouter, Cookie, Header, Request, Response, status

from jalada.dependencies import CurrentUser, ServicesDependency, session_token_from
from jalada.modules.accounts.api.schemas.auth import (
    SignInOptions,
    SignInRequest,
    SignUpRequest,
    UserResponse,
)
from jalada.modules.accounts.api.session_cookie import SESSION_COOKIE, set_session_cookie
from jalada.shared.http.errors import TooManyAttempts

router = APIRouter(tags=["auth"])


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
    set_session_cookie(request, response, issued)
    return UserResponse.from_user(issued.user)


@router.post("/v1/auth/login")
def sign_in(
    body: SignInRequest, request: Request, response: Response, services: ServicesDependency
) -> UserResponse:
    _check_rate(request, services, body.email)
    issued = services.authenticator.sign_in(body.email, body.password)
    set_session_cookie(request, response, issued)
    return UserResponse.from_user(issued.user)


@router.post("/v1/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def sign_out(
    response: Response,
    services: ServicesDependency,
    session_cookie: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
    # Left out of the contract: the same session as the cookie, for the desktop app.
    authorization: Annotated[str | None, Header(include_in_schema=False)] = None,
) -> None:
    session_token = session_token_from(session_cookie, authorization)
    if session_token:
        services.authenticator.sign_out(session_token)
    response.delete_cookie(SESSION_COOKIE)


@router.get("/v1/auth/providers")
def read_sign_in_options(services: ServicesDependency) -> SignInOptions:
    """Which ways to sign in are switched on, so the app only offers ones that work."""
    return SignInOptions(google=services.google_sign_in is not None)


@router.get("/v1/me")
def read_me(user: CurrentUser) -> UserResponse:
    return UserResponse.from_user(user)
