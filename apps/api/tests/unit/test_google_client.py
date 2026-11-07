import time
from typing import Any
from urllib.parse import parse_qs, urlparse

import pytest
from joserfc import jwt
from joserfc.jwk import KeySet, RSAKey

from jalada.modules.accounts.adapters.google import GoogleOpenIdClient
from jalada.shared.errors import GoogleSignInFailed

KEY = RSAKey.generate_key(2048, parameters={"kid": "test-key"})
OTHER_KEY = RSAKey.generate_key(2048, parameters={"kid": "test-key"})


def make_client() -> GoogleOpenIdClient:
    keys = KeySet([KEY]).as_dict(private=False)
    return GoogleOpenIdClient(
        "client-id",
        "client-secret",
        "http://localhost:3000/v1/auth/google/callback",
        fetch_keys=lambda: keys,
    )


def make_token(key: RSAKey = KEY, **overrides: Any) -> str:
    claims = {
        "iss": "https://accounts.google.com",
        "aud": "client-id",
        "sub": "google-123",
        "email": "jane@example.com",
        "email_verified": True,
        "name": "Jane Doe",
        "nonce": "the-nonce",
        "iat": int(time.time()),
        "exp": int(time.time()) + 300,
        **overrides,
    }
    return jwt.encode({"alg": "RS256", "kid": "test-key"}, claims, key)


def test_the_authorization_url_asks_for_an_id_token_with_pkce() -> None:
    url = make_client().authorization_url("the-state", "the-nonce", "v" * 48)

    query = parse_qs(urlparse(url).query)
    assert url.startswith("https://accounts.google.com/o/oauth2/v2/auth")
    assert query["client_id"] == ["client-id"]
    assert query["scope"] == ["openid email profile"]
    assert query["state"] == ["the-state"]
    assert query["nonce"] == ["the-nonce"]
    assert query["code_challenge_method"] == ["S256"]
    assert "code_challenge" in query
    assert "v" * 48 not in url, "the verifier itself never leaves the server"


def test_a_valid_id_token_becomes_a_profile() -> None:
    profile = make_client().read_id_token(make_token(), "the-nonce")

    assert profile.subject == "google-123"
    assert profile.email == "jane@example.com"
    assert profile.email_verified is True
    assert profile.name == "Jane Doe"


@pytest.mark.parametrize(
    "overrides",
    [
        {"aud": "someone-else"},
        {"iss": "https://evil.example.com"},
        {"nonce": "another-nonce"},
        {"exp": int(time.time()) - 60},
    ],
)
def test_tokens_with_wrong_claims_are_refused(overrides: dict[str, Any]) -> None:
    with pytest.raises(GoogleSignInFailed):
        make_client().read_id_token(make_token(**overrides), "the-nonce")


def test_a_token_signed_by_another_key_is_refused() -> None:
    with pytest.raises(GoogleSignInFailed):
        make_client().read_id_token(make_token(OTHER_KEY), "the-nonce")
