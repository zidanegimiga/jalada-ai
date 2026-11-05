from datetime import timedelta

import pytest
from fakes import FakeHasher, FixedClock, Store

from jalada.application.authentication import Authenticator
from jalada.application.errors import (
    EmailAlreadyRegistered,
    InvalidCredentials,
    NotSignedIn,
    WeakPassword,
)

PASSWORD = "correct horse battery"


def test_sign_up_saves_the_user_and_starts_a_session(
    authenticator: Authenticator, store: Store, clock: FixedClock
) -> None:
    issued = authenticator.sign_up(" Jane@Example.com ", PASSWORD, " Jane ")

    assert issued.user.email == "jane@example.com"
    assert issued.user.display_name == "Jane"
    assert issued.expires_at == clock.now() + timedelta(days=30)
    assert store.users[issued.user.id].password_hash == f"hashed:{PASSWORD}"
    assert issued.token not in store.sessions, "only the hash of the token is stored"
    assert authenticator.current_user(issued.token) == issued.user


def test_sign_up_refuses_an_email_that_is_taken(authenticator: Authenticator) -> None:
    authenticator.sign_up("jane@example.com", PASSWORD, "Jane")

    with pytest.raises(EmailAlreadyRegistered):
        authenticator.sign_up("JANE@example.com", PASSWORD, "Another Jane")


def test_sign_up_refuses_a_short_password(authenticator: Authenticator, store: Store) -> None:
    with pytest.raises(WeakPassword):
        authenticator.sign_up("jane@example.com", "short", "Jane")

    assert store.users == {}


def test_sign_in_with_the_right_password_starts_a_new_session(
    authenticator: Authenticator,
) -> None:
    signed_up = authenticator.sign_up("jane@example.com", PASSWORD, "Jane")

    signed_in = authenticator.sign_in("Jane@Example.com", PASSWORD)

    assert signed_in.user == signed_up.user
    assert signed_in.token != signed_up.token


def test_sign_in_with_a_wrong_password_fails(authenticator: Authenticator) -> None:
    authenticator.sign_up("jane@example.com", PASSWORD, "Jane")

    with pytest.raises(InvalidCredentials):
        authenticator.sign_in("jane@example.com", "wrong password")


def test_sign_in_with_an_unknown_email_still_checks_a_password(
    authenticator: Authenticator, hasher: FakeHasher
) -> None:
    with pytest.raises(InvalidCredentials):
        authenticator.sign_in("nobody@example.com", PASSWORD)

    assert len(hasher.verified) == 1, "a decoy hash is checked so timing does not reveal emails"


def test_sessions_stop_working_once_they_expire(
    authenticator: Authenticator, clock: FixedClock
) -> None:
    issued = authenticator.sign_up("jane@example.com", PASSWORD, "Jane")

    clock.current += timedelta(days=30, seconds=1)

    with pytest.raises(NotSignedIn):
        authenticator.current_user(issued.token)


def test_sign_out_ends_the_session(authenticator: Authenticator) -> None:
    issued = authenticator.sign_up("jane@example.com", PASSWORD, "Jane")

    authenticator.sign_out(issued.token)

    with pytest.raises(NotSignedIn):
        authenticator.current_user(issued.token)


def test_an_unknown_token_is_not_signed_in(authenticator: Authenticator) -> None:
    with pytest.raises(NotSignedIn):
        authenticator.current_user("made-up-token")
