import secrets
from datetime import timedelta
from uuid import UUID

import pytest
from fakes import FakeUnitOfWork, FixedClock, Store

from jalada.modules.accounts.application.authentication import Authenticator
from jalada.modules.accounts.application.device_sign_in import DeviceSignIn
from jalada.modules.accounts.domain.device_codes import challenge_for
from jalada.shared.errors import DeviceSignInFailed

VERIFIER = secrets.token_urlsafe(48)


@pytest.fixture
def device(store: Store, clock: FixedClock) -> DeviceSignIn:
    return DeviceSignIn(lambda: FakeUnitOfWork(store), clock, timedelta(days=30))


@pytest.fixture
def user_id(authenticator: Authenticator) -> UUID:
    return authenticator.sign_up("jane@example.com", "correct horse battery", "Jane").user.id


def test_the_app_holding_the_code_and_verifier_gets_a_session(
    device: DeviceSignIn, authenticator: Authenticator, user_id: UUID
) -> None:
    issued = device.issue_code(user_id, challenge_for(VERIFIER))

    session = device.exchange(issued.code, VERIFIER)

    assert session.user.id == user_id
    assert authenticator.current_user(session.token).id == user_id


def test_a_code_caught_on_its_way_is_useless_without_the_verifier(
    device: DeviceSignIn, user_id: UUID
) -> None:
    issued = device.issue_code(user_id, challenge_for(VERIFIER))

    with pytest.raises(DeviceSignInFailed):
        device.exchange(issued.code, secrets.token_urlsafe(48))


def test_a_code_works_once_even_after_a_wrong_verifier(device: DeviceSignIn, user_id: UUID) -> None:
    issued = device.issue_code(user_id, challenge_for(VERIFIER))
    with pytest.raises(DeviceSignInFailed):
        device.exchange(issued.code, secrets.token_urlsafe(48))

    with pytest.raises(DeviceSignInFailed):
        device.exchange(issued.code, VERIFIER)


def test_a_code_works_only_once(device: DeviceSignIn, user_id: UUID) -> None:
    issued = device.issue_code(user_id, challenge_for(VERIFIER))
    device.exchange(issued.code, VERIFIER)

    with pytest.raises(DeviceSignInFailed):
        device.exchange(issued.code, VERIFIER)


def test_a_code_expires_after_two_minutes(
    device: DeviceSignIn, clock: FixedClock, user_id: UUID
) -> None:
    issued = device.issue_code(user_id, challenge_for(VERIFIER))
    clock.current += timedelta(minutes=2, seconds=1)

    with pytest.raises(DeviceSignInFailed):
        device.exchange(issued.code, VERIFIER)


def test_only_the_stored_hash_of_a_code_is_kept(
    device: DeviceSignIn, store: Store, user_id: UUID
) -> None:
    issued = device.issue_code(user_id, challenge_for(VERIFIER))

    assert issued.code not in store.device_codes
    assert len(store.device_codes) == 1


def test_a_challenge_that_is_not_a_sha256_hash_is_refused(
    device: DeviceSignIn, user_id: UUID
) -> None:
    with pytest.raises(DeviceSignInFailed):
        device.issue_code(user_id, "plain")
