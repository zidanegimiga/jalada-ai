import importlib

import pytest

MODULES = ["accounts", "evidence", "pipeline", "ledger", "exports", "telegram", "health"]


@pytest.mark.parametrize(
    "package", ["core", "shared", "modules", *[f"modules.{m}" for m in MODULES]]
)
def test_each_package_says_what_belongs_in_it(package: str) -> None:
    module = importlib.import_module(f"jalada.{package}")

    assert module.__doc__, f"jalada.{package} should say what belongs in it"
