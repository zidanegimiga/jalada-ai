from dataclasses import dataclass

from jalada.api.rate_limit import RateLimiter
from jalada.application.authentication import Authenticator


@dataclass(frozen=True)
class Services:
    """Everything the routes need, built once in the composition root."""

    authenticator: Authenticator
    sign_in_limiter: RateLimiter
