from typing import Annotated

from fastapi import Cookie, Depends, Request

from jalada.modules.accounts.api.session_cookie import SESSION_COOKIE
from jalada.modules.accounts.domain.users import User
from jalada.services import Services
from jalada.shared.errors import NotSignedIn


def get_services(request: Request) -> Services:
    services: Services = request.app.state.services
    return services


def get_current_user(
    request: Request,
    services: Annotated[Services, Depends(get_services)],
    session_token: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
) -> User:
    if not session_token:
        raise NotSignedIn
    user = services.authenticator.current_user(session_token)
    # For the request's log line: who it was, by id only.
    request.state.user_id = str(user.id)
    return user


ServicesDependency = Annotated[Services, Depends(get_services)]
CurrentUser = Annotated[User, Depends(get_current_user)]
