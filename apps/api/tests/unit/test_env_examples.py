"""The example settings files must match what the code reads, so they never drift apart."""

from pathlib import Path

import pytest
import yaml

from jalada.config.settings import Settings

ROOT = Path(__file__).resolve().parents[4]
LOCAL = ROOT / ".env.example"
PRODUCTION = ROOT / ".env.production.example"
# Read outside the API's settings: by the web app, or by docker compose on your machine.
WEB_KEYS = ["API_URL", "NEXT_PUBLIC_SENTRY_DSN"]
LOCAL_ONLY_KEYS = ["POSTGRES_PASSWORD"]


def keys(path: Path) -> list[str]:
    lines = path.read_text().splitlines()
    return [line.split("=", 1)[0] for line in lines if line and not line.startswith("#")]


def setting_keys() -> set[str]:
    return {f"JALADA_{name.upper()}" for name in Settings.model_fields}


@pytest.mark.parametrize("path", [LOCAL, PRODUCTION], ids=["local", "production"])
def test_every_setting_the_code_reads_is_in_the_example(path: Path) -> None:
    listed = set(keys(path))

    assert setting_keys() - listed == set(), "settings missing from the example"
    assert listed - setting_keys() - set(WEB_KEYS) - set(LOCAL_ONLY_KEYS) == set(), "unknown keys"


def test_both_examples_list_the_same_settings_in_the_same_order() -> None:
    local = [key for key in keys(LOCAL) if key not in LOCAL_ONLY_KEYS]

    assert local == keys(PRODUCTION)


def test_no_key_is_listed_twice() -> None:
    for path in (LOCAL, PRODUCTION):
        assert len(keys(path)) == len(set(keys(path))), path.name


def test_the_render_blueprint_only_asks_for_known_production_settings() -> None:
    blueprint = yaml.safe_load((ROOT / "render.yaml").read_text())
    render_keys = {variable["key"] for variable in blueprint["services"][0]["envVars"]}
    required = {f"JALADA_{n.upper()}" for n, f in Settings.model_fields.items() if f.is_required()}

    assert render_keys <= set(keys(PRODUCTION))
    assert required <= render_keys, "a required setting is missing from render.yaml"


def test_the_production_example_holds_no_real_values() -> None:
    values = [
        line.split("=", 1)[1]
        for line in PRODUCTION.read_text().splitlines()
        if line and not line.startswith("#")
    ]
    secrets = [
        "JALADA_STORAGE_SECRET_KEY",
        "JALADA_GOOGLE_CLIENT_SECRET",
        "JALADA_TELEGRAM_BOT_TOKEN",
        "JALADA_EVIDENCE_KEYS",
    ]

    for key in secrets:
        value = dict(zip(keys(PRODUCTION), values, strict=True))[key]
        assert value.startswith("<") and value.endswith(">"), f"{key} must be a placeholder"
