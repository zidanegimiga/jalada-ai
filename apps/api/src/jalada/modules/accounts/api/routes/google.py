import re
from typing import Annotated

from fastapi import APIRouter, Cookie, Query, Request
from fastapi.responses import RedirectResponse

from jalada.dependencies import ServicesDependency
from jalada.modules.accounts.api.session_cookie import set_session_cookie
from jalada.modules.accounts.application.google_sign_in import GoogleAttempt
from jalada.shared.errors import GoogleSignInFailed

router = APIRouter(tags=["auth"])

ATTEMPT_COOKIE = "jalada_google"
# Where to go after signing in, such as the page that asks to sign the desktop app in.
RETURN_COOKIE = "jalada_google_next"
ATTEMPT_PATH = "/v1/auth/google"
# The same rule as the web app's safeReturnPath: a page of this site, never another one.
SAFE_RETURN = re.compile(r"^/(?![/\\])[^\s\\]*$")


def _return_path(raw: str | None) -> str | None:
    """A page of the web app to go back to, or None for anything else."""
    return raw if raw and len(raw) <= 2000 and SAFE_RETURN.match(raw) else None


def _to_web(request: Request, path: str) -> RedirectResponse:
    return RedirectResponse(f"{request.app.state.settings.public_url}{path}", status_code=302)


@router.get("/v1/auth/google/start")
def start_google_sign_in(
    request: Request,
    services: ServicesDependency,
    return_to: Annotated[str | None, Query(alias="next")] = None,
) -> RedirectResponse:
    if services.google_sign_in is None:
        return _to_web(request, "/signin?error=google_unavailable")
    url, attempt = services.google_sign_in.start()
    response = RedirectResponse(url, status_code=302)
    response.set_cookie(
        ATTEMPT_COOKIE,
        attempt.serialize(),
        max_age=600,
        path=ATTEMPT_PATH,
        httponly=True,
        secure=request.app.state.settings.cookie_secure,
        samesite="lax",
    )
    if back := _return_path(return_to):
        response.set_cookie(
            RETURN_COOKIE,
            back,
            max_age=600,
            path=ATTEMPT_PATH,
            httponly=True,
            secure=request.app.state.settings.cookie_secure,
            samesite="lax",
        )
    return response


@router.get("/v1/auth/google/callback")
def finish_google_sign_in(
    request: Request,
    services: ServicesDependency,
    code: str | None = None,
    state: str | None = None,
    attempt_cookie: Annotated[str | None, Cookie(alias=ATTEMPT_COOKIE)] = None,
    return_cookie: Annotated[str | None, Cookie(alias=RETURN_COOKIE)] = None,
) -> RedirectResponse:
    try:
        if not (services.google_sign_in and code and state and attempt_cookie):
            raise GoogleSignInFailed
        attempt = GoogleAttempt.parse(attempt_cookie)
        issued = services.google_sign_in.finish(attempt, state, code)
    except GoogleSignInFailed:
        response = _to_web(request, "/signin?error=google_failed")
    else:
        # A removed password matters more than the page: home, where the notice explains it.
        if issued.password_removed:
            response = _to_web(request, "/?notice=password_removed")
        else:
            response = _to_web(request, _return_path(return_cookie) or "/")
        set_session_cookie(request, response, issued)
    response.delete_cookie(ATTEMPT_COOKIE, path=ATTEMPT_PATH)
    response.delete_cookie(RETURN_COOKIE, path=ATTEMPT_PATH)
    return response
