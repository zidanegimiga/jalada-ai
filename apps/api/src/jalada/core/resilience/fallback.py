import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from jalada.core.resilience.breaker import CircuitBreaker
from jalada.core.resilience.failures import ProviderFailure
from jalada.core.resilience.retry import RetryPolicy


@dataclass(frozen=True)
class Attempt:
    """One call to one provider: what happened and how long it took."""

    provider: str
    outcome: str  # "ok" or a FailureKind value
    latency_ms: int


class AllProvidersFailed(Exception):
    def __init__(self, attempts: list[Attempt]) -> None:
        super().__init__(f"{len(attempts)} attempts, none succeeded")
        self.attempts = attempts


class FallbackChain[P]:
    """Chain of responsibility over providers of any kind.

    Each eligible provider gets a turn, in order. A failure worth retrying is retried on
    the same provider under the retry policy; any other failure, or running out of tries,
    passes the call to the next provider. Providers the circuit breaker has opened, and
    providers `eligible` rejects, are skipped. Errors that are not ProviderFailure are bugs
    and are raised at once.
    """

    def __init__(
        self,
        providers: Sequence[P],
        name_of: Callable[[P], str],
        retry: RetryPolicy,
        breaker: CircuitBreaker,
        sleep: Callable[[float], None] = time.sleep,
        timer: Callable[[], float] = time.perf_counter,
    ) -> None:
        self.providers = list(providers)
        self._name_of = name_of
        self._retry = retry
        self._breaker = breaker
        self._sleep = sleep
        self._timer = timer

    def run[R](
        self, call: Callable[[P], R], eligible: Callable[[P], bool] = lambda _: True
    ) -> tuple[R, P, list[Attempt]]:
        """The first result, the provider that gave it, and every attempt made."""
        attempts: list[Attempt] = []
        for provider in self.providers:
            name = self._name_of(provider)
            if not eligible(provider) or not self._breaker.allows(name):
                continue
            for try_number in range(1, self._retry.tries + 1):
                started = self._timer()
                try:
                    result = call(provider)
                except ProviderFailure as failure:
                    attempts.append(Attempt(name, failure.kind.value, self._elapsed(started)))
                    self._breaker.record_failure(name, failure.kind)
                    if not failure.retryable or try_number == self._retry.tries:
                        break
                    self._sleep(self._retry.wait_before(try_number, failure.retry_after))
                    continue
                attempts.append(Attempt(name, "ok", self._elapsed(started)))
                self._breaker.record_success(name)
                return result, provider, attempts
        raise AllProvidersFailed(attempts)

    def _elapsed(self, started: float) -> int:
        return round((self._timer() - started) * 1000)
