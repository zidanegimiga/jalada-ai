from collections.abc import Callable
from typing import cast

import httpx2
from authlib.integrations.httpx_client import OAuth2Client
from joserfc import jwt
from joserfc.errors import JoseError
from joserfc.jwk import KeySet, KeySetSerialization

from jalada.modules.accounts.application.ports import GoogleProfile
from jalada.shared.errors import GoogleSignInFailed

AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"  # noqa: S105 (an address, not a secret)
KEYS_URL = "https://www.googleapis.com/oauth2/v3/certs"
ISSUERS = ["https://accounts.google.com", "accounts.google.com"]


def fetch_google_keys() -> KeySetSerialization:
    response = httpx2.get(KEYS_URL, timeout=10)
    response.raise_for_status()
    return cast(KeySetSerialization, response.json())


class GoogleOpenIdClient:
    """Google sign-in with PKCE, checking the ID token's signature and claims ourselves."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        fetch_keys: Callable[[], KeySetSerialization] = fetch_google_keys,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri
        self._fetch_keys = fetch_keys

    def authorization_url(self, state: str, nonce: str, code_verifier: str) -> str:
        with self._oauth_client() as client:
            url, _ = client.create_authorization_url(
                AUTHORIZE_URL, state=state, nonce=nonce, code_verifier=code_verifier
            )
        return str(url)

    def exchange(self, code: str, nonce: str, code_verifier: str) -> GoogleProfile:
        try:
            with self._oauth_client() as client:
                token = client.fetch_token(TOKEN_URL, code=code, code_verifier=code_verifier)
            return self.read_id_token(token["id_token"], nonce)
        except (httpx2.HTTPError, KeyError, ValueError) as error:
            raise GoogleSignInFailed from error

    def read_id_token(self, id_token: str, nonce: str) -> GoogleProfile:
        try:
            token = jwt.decode(id_token, KeySet.import_key_set(self._fetch_keys()))
            jwt.JWTClaimsRegistry(
                iss={"essential": True, "values": ISSUERS},
                aud={"essential": True, "value": self._client_id},
                nonce={"essential": True, "value": nonce},
                sub={"essential": True},
                email={"essential": True},
            ).validate(token.claims)
        except JoseError as error:
            raise GoogleSignInFailed from error
        claims = token.claims
        return GoogleProfile(
            subject=str(claims["sub"]),
            email=str(claims["email"]),
            email_verified=claims.get("email_verified") is True,
            name=str(claims.get("name", "")),
        )

    def _oauth_client(self) -> OAuth2Client:
        return OAuth2Client(
            client_id=self._client_id,
            client_secret=self._client_secret,
            scope="openid email profile",
            redirect_uri=self._redirect_uri,
            code_challenge_method="S256",
            timeout=10,
        )
