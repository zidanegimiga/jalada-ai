import importlib

import pytest

LAYERS = ["domain", "application", "adapters", "pipeline", "api", "config"]


@pytest.mark.parametrize("layer", LAYERS)
def test_each_layer_is_an_importable_package(layer: str) -> None:
    module = importlib.import_module(f"jalada.{layer}")

    assert module.__doc__, f"jalada.{layer} should say what belongs in it"
