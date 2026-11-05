from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "test", "production"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR"]


class Settings(BaseSettings):
    """Runtime settings, read from JALADA_* environment variables.

    Values are checked when the object is built, so a missing or invalid
    setting stops the app at startup instead of failing later.
    """

    model_config = SettingsConfigDict(env_prefix="JALADA_", frozen=True)

    environment: Environment
    database_url: str = Field(pattern=r"^postgresql\+psycopg://")
    log_level: LogLevel = "INFO"
    session_days: int = Field(default=30, ge=1, le=365)
    # Browsers only send Secure cookies over HTTPS. Turn off for plain-HTTP local setups.
    cookie_secure: bool = True


def load_settings() -> Settings:
    """Build settings from the current environment. Call once, in the composition root."""
    return Settings()
