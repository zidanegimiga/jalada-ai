from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings, read from environment variables or a .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="LEDGER_", extra="ignore")

    database_url: str = "postgresql+psycopg://ledger:ledger@localhost:5432/ledger"
    evidence_dir: Path = Path("./data/evidence")

    # Phase 0 is a single-user tool: one owner, one API key.
    # Replace with real per-person login before inviting anyone else.
    owner_name: str = "Owner"
    owner_phone: str = ""
    api_key: str = "change-me"

    # Optional: enables photo and scanned-receipt extraction with Claude.
    anthropic_api_key: str | None = None
    vision_model: str = "claude-sonnet-5-5"


@lru_cache
def get_settings() -> Settings:
    return Settings()
