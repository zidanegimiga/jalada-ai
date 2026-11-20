"""One-time codes that sign a desktop app in through the browser (decision 0029).

The app makes a secret, the verifier, and sends only its SHA-256 hash, the challenge, with
the person to the browser (PKCE, RFC 7636). The code the browser hands back is useless
without the verifier, so a code caught on its way to the app cannot sign anyone in.
"""

import base64
import hashlib
import hmac
import re
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

# A SHA-256 hash in unpadded base64url is always 43 characters.
CHALLENGE = re.compile(r"^[A-Za-z0-9_-]{43}$")
# RFC 7636: 43 to 128 unreserved characters.
VERIFIER = re.compile(r"^[A-Za-z0-9._~-]{43,128}$")


@dataclass(frozen=True)
class DeviceCode:
    code_hash: str
    user_id: UUID
    challenge: str
    expires_at: datetime


def challenge_for(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


def verifier_matches(verifier: str, challenge: str) -> bool:
    """Compared in constant time, so timing says nothing about how close a guess was."""
    if not VERIFIER.match(verifier):
        return False
    return hmac.compare_digest(challenge_for(verifier), challenge)
