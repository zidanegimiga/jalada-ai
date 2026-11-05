from typing import Any

import pytest
import uvicorn

from jalada import serve

ENV = {
    "JALADA_ENVIRONMENT": "production",
    "JALADA_DATABASE_URL": "postgresql+psycopg://u:p@db.example.com:5432/jalada",
    "JALADA_STORAGE_ACCESS_KEY": "access",
    "JALADA_STORAGE_SECRET_KEY": "secret",
    "JALADA_EVIDENCE_KEYS": "a2V5",
}


@pytest.fixture
def calls(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, Any]]:
    seen: list[tuple[str, Any]] = []
    for name, value in ENV.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr(serve, "upgrade", lambda url: seen.append(("upgrade", url)))
    monkeypatch.setattr(serve, "ensure_bucket", lambda settings: seen.append(("bucket", None)))
    monkeypatch.setattr(uvicorn, "run", lambda app, **options: seen.append(("run", options)))
    return seen


def test_the_server_uses_the_hosts_port_and_reads_forwarded_addresses(
    calls: list[tuple[str, Any]], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PORT", "10000")

    serve.main()

    [(name, options)] = calls
    assert name == "run"
    assert options["port"] == 10000
    assert options["factory"] is True
    assert options["proxy_headers"] is True


def test_migrations_and_the_bucket_check_run_first_when_asked(
    calls: list[tuple[str, Any]], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("JALADA_MIGRATE_ON_START", "true")

    serve.main()

    assert [name for name, _ in calls] == ["upgrade", "bucket", "run"]
