from datetime import datetime

from pydantic import BaseModel


class LinkCodeResponse(BaseModel):
    code: str
    expires_at: datetime
    # Opens the bot in Telegram with the code filled in. None when the bot is not set up.
    bot_link: str | None


class TelegramStatus(BaseModel):
    available: bool
    linked: bool
