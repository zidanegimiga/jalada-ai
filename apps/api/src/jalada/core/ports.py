from datetime import datetime
from typing import Protocol


class Limiter(Protocol):
    """Counts attempts per key. False once any key is over its limit."""

    def allow(self, *keys: str) -> bool: ...


class HealthCheck(Protocol):
    """Something the API depends on, checked by /health/ready."""

    name: str

    def ok(self) -> bool: ...


class Clock(Protocol):
    def now(self) -> datetime: ...
