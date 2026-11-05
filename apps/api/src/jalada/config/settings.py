from decimal import Decimal
from typing import Literal, Self

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "test", "production"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR"]
ModelProvider = Literal["none", "gemini", "ollama"]
DEFAULT_MODELS = {"gemini": "gemini-2.5-flash", "ollama": "qwen2.5vl:3b"}


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
    # The language model used when rules cannot read or classify evidence.
    model_provider: ModelProvider = "none"
    model_name: str | None = None
    gemini_api_key: SecretStr | None = None
    ollama_url: str = "http://localhost:11434"
    # US dollars per million tokens, for the cost recorded on each run. Zero on free tiers.
    model_input_price: Decimal = Field(default=Decimal(0), ge=0)
    model_output_price: Decimal = Field(default=Decimal(0), ge=0)
    # Set to true only for a provider whose terms exclude training on the data sent to it.
    model_allowed_for_real_data: bool = False
    # Telegram bot. Switched off unless the token and the bot's username are both set.
    telegram_bot_token: SecretStr | None = None
    telegram_bot_username: str | None = None
    # Telegram sends this back on every webhook call, so the API can tell the call is real.
    telegram_webhook_secret: SecretStr | None = None
    # Run the job loop inside the API process, for hosts with no separate background workers.
    run_worker_in_api: bool = False
    # Apply migrations and check the evidence bucket when the API starts, for hosts with no
    # separate release step.
    migrate_on_start: bool = False
    # Limits for one piece of evidence.
    pipeline_max_attempts: int = Field(default=3, ge=1, le=5)
    pipeline_max_tokens: int = Field(default=8000, ge=0)
    pipeline_max_cost_usd: Decimal = Field(default=Decimal("0.02"), ge=0)

    @model_validator(mode="after")
    def check_model_settings(self) -> Self:
        if self.model_provider == "gemini" and self.gemini_api_key is None:
            raise ValueError("JALADA_GEMINI_API_KEY is needed for the gemini provider")
        uses_model = self.model_provider != "none"
        if self.environment == "production" and uses_model and not self.model_allowed_for_real_data:
            raise ValueError(
                "Real users' evidence may only go to a provider whose terms exclude training on "
                "it (decision 0012). Set JALADA_MODEL_ALLOWED_FOR_REAL_DATA=true once that is so."
            )
        return self

    @property
    def resolved_model_name(self) -> str:
        return self.model_name or DEFAULT_MODELS.get(self.model_provider, "")


def load_settings() -> Settings:
    """Build settings from the current environment. Call once, in the composition root."""
    return Settings()
