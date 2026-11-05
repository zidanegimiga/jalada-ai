from limits import parse
from limits.storage import MemoryStorage
from limits.strategies import MovingWindowRateLimiter


class RateLimiter:
    """Counts attempts per key, for example per IP address and per email address."""

    def __init__(self, rule: str) -> None:
        self._rule = parse(rule)
        self._limiter = MovingWindowRateLimiter(MemoryStorage())

    def allow(self, *keys: str) -> bool:
        """Record one attempt against every key. False if any key is over its limit."""
        results = [self._limiter.hit(self._rule, key) for key in keys]
        return all(results)
