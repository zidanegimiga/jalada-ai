import time
from collections.abc import Callable
from dataclasses import dataclass, field

from jalada.core.resilience.failures import FailureKind


@dataclass
class _State:
    failures: int = 0
    opened_at: float | None = None


@dataclass
class CircuitBreaker:
    """Skips a provider that keeps failing, so every call does not pay for its timeout.

    After `threshold` failures in a row the provider is skipped for `cool_down` seconds,
    then given another chance. A misconfigured provider, such as one with a wrong key, is
    skipped at once: retrying cannot fix it.
    """

    threshold: int = 3
    cool_down: float = 60.0
    clock: Callable[[], float] = time.monotonic
    _states: dict[str, _State] = field(default_factory=dict)

    def allows(self, provider: str) -> bool:
        state = self._states.get(provider)
        if state is None or state.opened_at is None:
            return True
        if self.clock() - state.opened_at >= self.cool_down:
            state.opened_at = None
            state.failures = self.threshold - 1  # one more failure opens it again
            return True
        return False

    def record_success(self, provider: str) -> None:
        self._states.pop(provider, None)

    def record_failure(self, provider: str, kind: FailureKind) -> None:
        state = self._states.setdefault(provider, _State())
        state.failures += 1
        if kind == FailureKind.MISCONFIGURED or state.failures >= self.threshold:
            state.opened_at = self.clock()
