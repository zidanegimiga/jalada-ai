import pytest
from pydantic import ValidationError

from jalada.config.settings import load_settings


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("JALADA_ENVIRONMENT", raising=False)
    monkeypatch.delenv("JALADA_LOG_LEVEL", raising=False)


def test_loads_values_from_prefixed_environment_variables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("JALADA_ENVIRONMENT", "production")
    monkeypatch.setenv("JALADA_LOG_LEVEL", "WARNING")

    settings = load_settings()

    assert settings.environment == "production"
    assert settings.log_level == "WARNING"


def test_log_level_defaults_to_info(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JALADA_ENVIRONMENT", "test")

    assert load_settings().log_level == "INFO"


def test_missing_environment_stops_startup() -> None:
    with pytest.raises(ValidationError, match="environment"):
        load_settings()


@pytest.mark.parametrize(
    ("variable", "value"),
    [("JALADA_ENVIRONMENT", "staging"), ("JALADA_LOG_LEVEL", "LOUD")],
)
def test_unknown_values_are_rejected(
    monkeypatch: pytest.MonkeyPatch, variable: str, value: str
) -> None:
    monkeypatch.setenv("JALADA_ENVIRONMENT", "test")
    monkeypatch.setenv(variable, value)

    with pytest.raises(ValidationError):
        load_settings()


def test_settings_cannot_be_changed_after_loading(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JALADA_ENVIRONMENT", "test")
    settings = load_settings()

    with pytest.raises(ValidationError):
        settings.log_level = "DEBUG"  # type: ignore[misc]
