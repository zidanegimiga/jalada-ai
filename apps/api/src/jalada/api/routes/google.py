from typing import Annotated

from fastapi import APIRouter, Cookie, Request
from fastapi.responses import RedirectResponse

from jalada.api.dependencies import ServicesDependency
from jalada.api.session_cookie import set_session_cookie
from jalada.application.errors import GoogleSignInFailed
from jalada.application.google_sign_in import GoogleAttempt

router = APIRouter(tags=["auth"])

ATTEMPT_COOKIE = "jalada_google"
ATTEMPT_PATH = "/v1/auth/google"


def _to_web(request: Request, path: str) -> RedirectResponse:
    return RedirectResponse(f"{request.app.state.settings.public_url}{path}", status_code=302)


@router.get("/v1/auth/google/start")
def start_google_sign_in(request: Request, services: ServicesDependency) -> RedirectResponse:
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
    return response


@router.get("/v1/auth/google/callback")
def finish_google_sign_in(
    request: Request,
    services: ServicesDependency,
    code: str | None = None,
    state: str | None = None,
    attempt_cookie: Annotated[str | None, Cookie(alias=ATTEMPT_COOKIE)] = None,
) -> RedirectResponse:
    try:
        if not (services.google_sign_in and code and state and attempt_cookie):
            raise GoogleSignInFailed
        attempt = GoogleAttempt.parse(attempt_cookie)
        issued = services.google_sign_in.finish(attempt, state, code)
    except GoogleSignInFailed:
        response = _to_web(request, "/signin?error=google_failed")
    else:
        response = _to_web(request, "/?notice=password_removed" if issued.password_removed else "/")
        set_session_cookie(request, response, issued)
    response.delete_cookie(ATTEMPT_COOKIE, path=ATTEMPT_PATH)
    return response
