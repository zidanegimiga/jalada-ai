from typing import Annotated

from fastapi import Cookie, Depends, Header, Request

from jalada.modules.accounts.api.session_cookie import SESSION_COOKIE
from jalada.modules.accounts.domain.users import User
from jalada.services import Services
from jalada.shared.errors import NotSignedIn


def get_services(request: Request) -> Services:
    services: Services = request.app.state.services
    return services


def session_token_from(cookie: str | None, authorization: str | None) -> str | None:
    """The web app sends its session as a cookie; the desktop app, which has no cookies of
    the site's, sends the same kind of session as a Bearer token (decision 0029)."""
    if cookie:
        return cookie
    scheme, _, token = (authorization or "").partition(" ")
    return token.strip() or None if scheme.lower() == "bearer" else None


def session_token_of(request: Request) -> str | None:
    return session_token_from(
        request.cookies.get(SESSION_COOKIE), request.headers.get("authorization")
    )


def get_current_user(
    request: Request,
    services: Annotated[Services, Depends(get_services)],
    session_cookie: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
    # Left out of the contract: the same session as the cookie, for the desktop app.
    authorization: Annotated[str | None, Header(include_in_schema=False)] = None,
) -> User:
    session_token = session_token_from(session_cookie, authorization)
    if not session_token:
        raise NotSignedIn
    user = services.authenticator.current_user(session_token)
    # For the request's log line: who it was, by id only.
    request.state.user_id = str(user.id)
    return user


ServicesDependency = Annotated[Services, Depends(get_services)]
CurrentUser = Annotated[User, Depends(get_current_user)]
