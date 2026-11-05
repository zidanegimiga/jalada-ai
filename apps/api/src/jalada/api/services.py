from dataclasses import dataclass

from jalada.api.rate_limit import RateLimiter
from jalada.application.authentication import Authenticator
from jalada.application.google_sign_in import GoogleSignIn


@dataclass(frozen=True)
class Services:
    """Everything the routes need, built once in the composition root."""

    authenticator: Authenticator
    sign_in_limiter: RateLimiter
    # None when Google sign-in is not configured.
    google_sign_in: GoogleSignIn | None = None
