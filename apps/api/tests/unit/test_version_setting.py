import pytest

from jalada.config.settings import Settings

REQUIRED = {
    "JALADA_ENVIRONMENT": "test",
    "JALADA_DATABASE_URL": "postgresql+psycopg://u:p@localhost/db",
    "JALADA_STORAGE_ACCESS_KEY": "key",
    "JALADA_STORAGE_SECRET_KEY": "secret",
    "JALADA_EVIDENCE_KEYS": "a2V5",
}


@pytest.fixture(autouse=True)
def required(monkeypatch: pytest.MonkeyPatch) -> None:
    for name, value in REQUIRED.items():
        monkeypatch.setenv(name, value)
    monkeypatch.delenv("JALADA_VERSION", raising=False)
    monkeypatch.delenv("RENDER_GIT_COMMIT", raising=False)


def test_the_version_comes_from_render_when_not_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RENDER_GIT_COMMIT", "abc1234def")

    assert Settings().version == "abc1234def"


def test_an_explicit_version_wins_and_an_empty_one_means_development(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RENDER_GIT_COMMIT", "abc1234def")
    monkeypatch.setenv("JALADA_VERSION", "1.2.0")
    assert Settings().version == "1.2.0"

    monkeypatch.setenv("JALADA_VERSION", " ")
    monkeypatch.delenv("RENDER_GIT_COMMIT")
    assert Settings().version == "development"
