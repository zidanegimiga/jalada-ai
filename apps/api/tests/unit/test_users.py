import pytest

from jalada.modules.accounts.domain.sessions import hash_session_token
from jalada.modules.accounts.domain.users import is_acceptable_password, normalize_email


def test_emails_are_trimmed_and_lowercased() -> None:
    assert normalize_email("  Jane.Doe@Example.COM ") == "jane.doe@example.com"


@pytest.mark.parametrize(
    ("password", "acceptable"),
    [("a" * 9, False), ("a" * 10, True), ("a" * 128, True), ("a" * 129, False)],
)
def test_passwords_must_be_10_to_128_characters(password: str, acceptable: bool) -> None:
    assert is_acceptable_password(password) is acceptable


def test_session_tokens_are_stored_as_a_fixed_sha256_hash() -> None:
    hashed = hash_session_token("token")

    assert hashed == hash_session_token("token")
    assert hashed != "token"
    assert len(hashed) == 64
