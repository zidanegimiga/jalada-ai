from jalada.modules.agent.adapters.orchestration.checkpoints import connection_settings


def test_no_startup_option_is_sent_without_a_schema() -> None:
    # Neon's pooler, used in production, refuses the connection when one is sent.
    assert "options" not in connection_settings(None)


def test_a_schema_is_set_when_asked_for() -> None:
    assert connection_settings("assistant_turns_test")["options"] == (
        "-c search_path=assistant_turns_test"
    )


def test_statements_are_never_prepared() -> None:
    assert connection_settings(None)["prepare_threshold"] == 0
