import os

import pytest
from pydantic import ValidationError

from jalada.core.settings import load_settings

DATABASE_URL = "postgresql+psycopg://user:pass@localhost:5432/jalada"


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in list(os.environ):
        if name.startswith("JALADA_"):
            monkeypatch.delenv(name)


@pytest.fixture
def minimal_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JALADA_ENVIRONMENT", "test")
    monkeypatch.setenv("JALADA_DATABASE_URL", DATABASE_URL)
    monkeypatch.setenv("JALADA_STORAGE_ACCESS_KEY", "access")
    monkeypatch.setenv("JALADA_STORAGE_SECRET_KEY", "s3-password-value")
    monkeypatch.setenv("JALADA_EVIDENCE_KEYS", "a2V5")


@pytest.mark.usefixtures("minimal_environment")
def test_loads_values_from_prefixed_environment_variables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("JALADA_LOG_LEVEL", "WARNING")
    monkeypatch.setenv("JALADA_SESSION_DAYS", "7")

    settings = load_settings()

    assert settings.database_url == DATABASE_URL
    assert settings.log_level == "WARNING"
    assert settings.session_days == 7


@pytest.mark.usefixtures("minimal_environment")
def test_defaults_are_safe() -> None:
    settings = load_settings()

    assert settings.log_level == "INFO"
    assert settings.session_days == 30
    assert settings.cookie_secure is True
    assert settings.google_client_id is None
    assert settings.storage_endpoint_url is None
    assert "s3-password-value" not in repr(settings), "secrets never appear when printed"


@pytest.mark.parametrize(
    "missing", ["JALADA_ENVIRONMENT", "JALADA_DATABASE_URL", "JALADA_EVIDENCE_KEYS"]
)
@pytest.mark.usefixtures("minimal_environment")
def test_required_settings_stop_startup_when_missing(
    monkeypatch: pytest.MonkeyPatch, missing: str
) -> None:
    monkeypatch.delenv(missing)

    with pytest.raises(ValidationError):
        load_settings()


@pytest.mark.parametrize(
    ("variable", "value"),
    [
        ("JALADA_ENVIRONMENT", "staging"),
        ("JALADA_LOG_LEVEL", "LOUD"),
        ("JALADA_DATABASE_URL", "sqlite:///jalada.db"),
        ("JALADA_SESSION_DAYS", "0"),
    ],
)
@pytest.mark.usefixtures("minimal_environment")
def test_unknown_values_are_rejected(
    monkeypatch: pytest.MonkeyPatch, variable: str, value: str
) -> None:
    monkeypatch.setenv(variable, value)

    with pytest.raises(ValidationError):
        load_settings()


@pytest.mark.usefixtures("minimal_environment")
def test_settings_cannot_be_changed_after_loading() -> None:
    settings = load_settings()

    with pytest.raises(ValidationError):
        settings.log_level = "DEBUG"  # type: ignore[misc]
