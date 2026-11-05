from typing import Literal

from pydantic import Field, SecretStr
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
    # The address users open in their browser. Google sends them back here after sign-in.
    public_url: str = Field(default="http://localhost:3000", pattern=r"^https?://[^/]+$")
    # Google sign-in is switched off unless both are set.
    google_client_id: str | None = None
    google_client_secret: SecretStr | None = None
    # Evidence storage in any S3-compatible bucket. Leave the endpoint empty for Amazon S3.
    storage_endpoint_url: str | None = None
    storage_bucket: str = "jalada-evidence"
    storage_region: str = "us-east-1"
    storage_access_key: str
    storage_secret_key: SecretStr
    # Base64 encoded 32-byte keys, comma separated. The first encrypts new evidence.
    # Keep older keys after the first so evidence encrypted with them can still be read.
    evidence_keys: SecretStr


def load_settings() -> Settings:
    """Build settings from the current environment. Call once, in the composition root."""
    return Settings()
