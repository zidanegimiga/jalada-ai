import pytest
from fakes import FakeGoogle, Store

from jalada.application.authentication import Authenticator
from jalada.application.errors import GoogleSignInFailed
from jalada.application.google_sign_in import GoogleAttempt, GoogleSignIn
from jalada.application.ports import GoogleProfile

PROFILE = GoogleProfile("google-123", "Jane@Example.com", True, "Jane Doe")


def test_a_new_google_user_gets_an_account_without_a_password(
    authenticator: Authenticator, store: Store
) -> None:
    issued = authenticator.sign_in_with_google(PROFILE)

    assert issued.user.email == "jane@example.com"
    assert issued.user.display_name == "Jane Doe"
    assert store.users[issued.user.id].password_hash is None
    assert store.google_subjects["google-123"] == issued.user.id


def test_a_returning_google_user_gets_the_same_account(authenticator: Authenticator) -> None:
    first = authenticator.sign_in_with_google(PROFILE)

    again = authenticator.sign_in_with_google(PROFILE)

    assert again.user == first.user


def test_google_links_to_an_existing_account_with_the_same_email(
    authenticator: Authenticator, store: Store
) -> None:
    existing = authenticator.sign_up("jane@example.com", "correct horse battery", "Jane")

    issued = authenticator.sign_in_with_google(PROFILE)

    assert issued.user == existing.user
    assert store.google_subjects["google-123"] == existing.user.id
    assert authenticator.sign_in("jane@example.com", "correct horse battery").user == existing.user


def test_an_unverified_google_email_is_refused(authenticator: Authenticator, store: Store) -> None:
    unverified = GoogleProfile("google-123", "jane@example.com", False, "Jane")

    with pytest.raises(GoogleSignInFailed):
        authenticator.sign_in_with_google(unverified)

    assert store.users == {}


def test_a_missing_name_falls_back_to_the_email_name(authenticator: Authenticator) -> None:
    issued = authenticator.sign_in_with_google(GoogleProfile("g-1", "amina@example.com", True, " "))

    assert issued.user.display_name == "amina"


def test_finish_refuses_a_state_that_does_not_match(
    authenticator: Authenticator, google: FakeGoogle
) -> None:
    flow = GoogleSignIn(google, authenticator)
    _, attempt = flow.start()

    with pytest.raises(GoogleSignInFailed):
        flow.finish(attempt, "someone-elses-state", "good-code")

    assert google.exchanged == [], "the code is never exchanged when the state is wrong"


def test_finish_passes_the_nonce_and_verifier_from_start(
    authenticator: Authenticator, google: FakeGoogle
) -> None:
    flow = GoogleSignIn(google, authenticator)
    _, attempt = flow.start()

    flow.finish(attempt, attempt.state, "good-code")

    assert google.exchanged == [("good-code", attempt.nonce, attempt.code_verifier)]


@pytest.mark.parametrize("value", ["", "a.b", "a..c", "a.b.c.d"])
def test_a_damaged_attempt_cookie_is_refused(value: str) -> None:
    with pytest.raises(GoogleSignInFailed):
        GoogleAttempt.parse(value)


def test_an_attempt_survives_a_round_trip_through_the_cookie() -> None:
    attempt = GoogleAttempt("state", "nonce", "verifier")

    assert GoogleAttempt.parse(attempt.serialize()) == attempt
