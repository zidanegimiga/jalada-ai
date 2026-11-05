from fastapi import Request, Response

from jalada.application.authentication import IssuedSession

SESSION_COOKIE = "jalada_session"


def set_session_cookie(request: Request, response: Response, issued: IssuedSession) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        issued.token,
        expires=issued.expires_at,
        httponly=True,
        secure=request.app.state.settings.cookie_secure,
        samesite="lax",
    )
