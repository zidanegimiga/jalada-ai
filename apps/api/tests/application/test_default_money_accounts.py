import pytest
from fakes import Store

from jalada.modules.accounts.application.authentication import Authenticator
from jalada.modules.accounts.application.ports import GoogleProfile
from jalada.shared.errors import EmailAlreadyRegistered

PASSWORD = "correct horse battery"
PROFILE = GoogleProfile("google-123", "jane@example.com", True, "Jane")


def names(store: Store) -> list[tuple[str, str]]:
    return sorted((str(a.user_id), a.name) for a in store.money_accounts.values())


def test_signing_up_opens_mpesa_and_cash(authenticator: Authenticator, store: Store) -> None:
    user = authenticator.sign_up("jane@example.com", PASSWORD, "Jane").user

    assert names(store) == [(str(user.id), "Cash"), (str(user.id), "M-Pesa")]
    assert all(a.created_at == user.created_at for a in store.money_accounts.values())


def test_a_new_google_user_gets_them_too(authenticator: Authenticator, store: Store) -> None:
    user = authenticator.sign_in_with_google(PROFILE).user

    assert names(store) == [(str(user.id), "Cash"), (str(user.id), "M-Pesa")]


def test_signing_in_again_or_linking_google_opens_nothing_more(
    authenticator: Authenticator, store: Store
) -> None:
    authenticator.sign_up("jane@example.com", PASSWORD, "Jane")
    authenticator.sign_in("jane@example.com", PASSWORD)
    authenticator.sign_in_with_google(PROFILE)
    authenticator.sign_in_with_google(PROFILE)

    assert len(store.money_accounts) == 2


def test_a_refused_sign_up_opens_nothing(authenticator: Authenticator, store: Store) -> None:
    authenticator.sign_up("jane@example.com", PASSWORD, "Jane")

    with pytest.raises(EmailAlreadyRegistered):
        authenticator.sign_up("jane@example.com", PASSWORD, "Someone")

    assert len(store.money_accounts) == 2
