"""Builds the accounts module's use cases from the pieces the composition root shares."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import timedelta

from jalada.core.ports import Clock
from jalada.modules.accounts.adapters.account_archive import ZipAccountArchive
from jalada.modules.accounts.adapters.argon2_hasher import Argon2PasswordHasher
from jalada.modules.accounts.adapters.google import GoogleOpenIdClient
from jalada.modules.accounts.application.account_deletion import AccountDeletion
from jalada.modules.accounts.application.account_export import AccountExport
from jalada.modules.accounts.application.authentication import Authenticator, UserCreated
from jalada.modules.accounts.application.device_sign_in import DeviceSignIn
from jalada.modules.accounts.application.google_sign_in import GoogleSignIn
from jalada.modules.evidence.application.ports import EvidenceStore
from jalada.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class GoogleClient:
    """The Google OAuth client registered for this site."""

    client_id: str
    client_secret: str
    redirect_uri: str


@dataclass(frozen=True)
class AccountServices:
    authenticator: Authenticator
    account_export: AccountExport
    account_deletion: AccountDeletion
    device_sign_in: DeviceSignIn
    # None when Google sign-in is not configured.
    google_sign_in: GoogleSignIn | None


def build_accounts(
    unit_of_work: Callable[[], UnitOfWork],
    clock: Clock,
    store: EvidenceStore,
    session_days: int,
    on_user_created: Sequence[UserCreated],
    google: GoogleClient | None,
) -> AccountServices:
    authenticator = Authenticator(
        unit_of_work=unit_of_work,
        hasher=Argon2PasswordHasher(),
        clock=clock,
        session_lifetime=timedelta(days=session_days),
        on_user_created=on_user_created,
    )
    return AccountServices(
        authenticator=authenticator,
        account_export=AccountExport(unit_of_work, store, ZipAccountArchive()),
        account_deletion=AccountDeletion(unit_of_work, store),
        device_sign_in=DeviceSignIn(unit_of_work, clock, timedelta(days=session_days)),
        google_sign_in=build_google_sign_in(google, authenticator),
    )


def build_google_sign_in(
    google: GoogleClient | None, authenticator: Authenticator
) -> GoogleSignIn | None:
    if google is None:
        return None
    client = GoogleOpenIdClient(
        client_id=google.client_id,
        client_secret=google.client_secret,
        redirect_uri=google.redirect_uri,
    )
    return GoogleSignIn(client, authenticator)
