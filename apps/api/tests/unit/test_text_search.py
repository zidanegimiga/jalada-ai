from jalada.core.database.text_search import contains_pattern


def test_the_persons_wildcards_match_only_themselves() -> None:
    assert contains_pattern("50%_off") == "%50\\%\\_off%"
    assert contains_pattern("a\\b") == "%a\\\\b%"
