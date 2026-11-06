from jalada.contract import CONTRACT, as_text, openapi_document


def test_the_api_matches_its_committed_contract() -> None:
    """If this fails after changing the API on purpose, run `make openapi` and commit
    apps/api/openapi.json. The web app's types are generated from it (make web-types)."""
    assert CONTRACT.read_text() == as_text(openapi_document())
