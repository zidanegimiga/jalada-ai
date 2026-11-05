import secrets
from typing import Annotated, Any

from fastapi import APIRouter, Body, Header, HTTPException, Request

from jalada.api.dependencies import CurrentUser, ServicesDependency
from jalada.api.schemas.telegram import LinkCodeResponse, TelegramStatus

router = APIRouter(tags=["telegram"])


def _bot_username(request: Request) -> str | None:
    username: str | None = request.app.state.settings.telegram_bot_username
    return username


@router.get("/v1/telegram/status")
def read_telegram_status(
    request: Request, user: CurrentUser, services: ServicesDependency
) -> TelegramStatus:
    return TelegramStatus(
        available=_bot_username(request) is not None,
        linked=services.telegram_linking.is_linked(user.id),
    )


@router.post("/v1/telegram/link-code")
def create_link_code(
    request: Request, user: CurrentUser, services: ServicesDependency
) -> LinkCodeResponse:
    issued = services.telegram_linking.new_code(user.id)
    username = _bot_username(request)
    link = f"https://t.me/{username}?start={issued.code}" if username else None
    return LinkCodeResponse(code=issued.code, expires_at=issued.expires_at, bot_link=link)


@router.post("/v1/telegram/webhook", include_in_schema=False)
def receive_telegram_update(
    request: Request,
    services: ServicesDependency,
    update: Annotated[dict[str, Any], Body()],
    secret: Annotated[str | None, Header(alias="X-Telegram-Bot-Api-Secret-Token")] = None,
) -> dict[str, bool]:
    """Called by Telegram for each message sent to the bot."""
    expected = request.app.state.settings.telegram_webhook_secret
    if services.telegram_capture is None or expected is None:
        raise HTTPException(status_code=404)
    if not secret or not secrets.compare_digest(secret, expected.get_secret_value()):
        raise HTTPException(status_code=401)
    services.telegram_capture.handle(update)
    return {"ok": True}
