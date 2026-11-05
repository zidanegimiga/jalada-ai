from fastapi import APIRouter, Request

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
