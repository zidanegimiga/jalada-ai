import secrets
from dataclasses import dataclass

from jalada.application.authentication import Authenticator, IssuedSession
from jalada.application.errors import GoogleSignInFailed
from jalada.application.ports import GoogleIdentity


@dataclass(frozen=True)
class GoogleAttempt:
    """Random values that tie Google's reply to the browser that started sign-in."""

    state: str
    nonce: str
    code_verifier: str

    def serialize(self) -> str:
        return ".".join((self.state, self.nonce, self.code_verifier))

    @classmethod
    def parse(cls, value: str) -> "GoogleAttempt":
        parts = value.split(".")
        if len(parts) != 3 or not all(parts):
            raise GoogleSignInFailed
        return cls(*parts)


class GoogleSignIn:
    def __init__(self, google: GoogleIdentity, authenticator: Authenticator) -> None:
        self._google = google
        self._authenticator = authenticator

    def start(self) -> tuple[str, GoogleAttempt]:
        attempt = GoogleAttempt(
            secrets.token_urlsafe(24), secrets.token_urlsafe(24), secrets.token_urlsafe(48)
        )
        url = self._google.authorization_url(attempt.state, attempt.nonce, attempt.code_verifier)
        return url, attempt

    def finish(self, attempt: GoogleAttempt, returned_state: str, code: str) -> IssuedSession:
        if not secrets.compare_digest(attempt.state, returned_state):
            raise GoogleSignInFailed
        profile = self._google.exchange(code, attempt.nonce, attempt.code_verifier)
        return self._authenticator.sign_in_with_google(profile)
