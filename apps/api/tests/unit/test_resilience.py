import pytest

from jalada.core.resilience.breaker import CircuitBreaker
from jalada.core.resilience.failures import FailureKind, ProviderFailure
from jalada.core.resilience.fallback import AllProvidersFailed, Attempt, FallbackChain
from jalada.core.resilience.retry import RetryPolicy

NO_JITTER = RetryPolicy(tries=2, base_delay=1.0, max_delay=8.0, jitter=lambda: 1.0)


class Script:
    """A provider that answers with whatever it is told to, in order."""

    def __init__(self, name: str, *outcomes: str | ProviderFailure) -> None:
        self.name = name
        self.outcomes = list(outcomes)
        self.calls = 0

    def __call__(self) -> str:
        self.calls += 1
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, ProviderFailure):
            raise outcome
        return outcome


def chain(
    *providers: Script, breaker: CircuitBreaker | None = None
) -> tuple[FallbackChain[Script], list[float]]:
    waits: list[float] = []
    return (
        FallbackChain(
            providers,
            lambda p: p.name,
            NO_JITTER,
            breaker or CircuitBreaker(),
            sleep=waits.append,
            timer=lambda: 0.0,
        ),
        waits,
    )


def test_the_first_provider_that_answers_wins() -> None:
    primary, backup = Script("primary", "answer"), Script("backup", "other")
    fallback, _ = chain(primary, backup)

    result, used, attempts = fallback.run(lambda p: p())

    assert (result, used) == ("answer", primary)
    assert attempts == [Attempt("primary", "ok", 0)]
    assert backup.calls == 0


def test_a_rate_limit_is_retried_after_the_wait_the_provider_asked_for() -> None:
    primary = Script("primary", ProviderFailure(FailureKind.RATE_LIMITED, retry_after=3), "answer")
    fallback, waits = chain(primary)

    result, _, attempts = fallback.run(lambda p: p())

    assert result == "answer"
    assert waits == [3]
    assert [a.outcome for a in attempts] == ["rate_limited", "ok"]


def test_a_provider_that_stays_down_hands_over_to_the_next() -> None:
    down = ProviderFailure(FailureKind.UNAVAILABLE)
    primary, backup = Script("primary", down, down), Script("backup", "answer")
    fallback, waits = chain(primary, backup)

    result, used, attempts = fallback.run(lambda p: p())

    assert (result, used) == ("answer", backup)
    assert waits == [1.0], "one retry with backoff, then the next provider"
    assert [(a.provider, a.outcome) for a in attempts] == [
        ("primary", "unavailable"),
        ("primary", "unavailable"),
        ("backup", "ok"),
    ]


@pytest.mark.parametrize(
    "kind",
    [FailureKind.BAD_OUTPUT, FailureKind.TOO_LARGE, FailureKind.REFUSED, FailureKind.MISCONFIGURED],
)
def test_failures_that_retrying_cannot_fix_go_straight_to_the_next(kind: FailureKind) -> None:
    primary, backup = Script("primary", ProviderFailure(kind)), Script("backup", "answer")
    fallback, waits = chain(primary, backup)

    result, _, _ = fallback.run(lambda p: p())

    assert result == "answer"
    assert primary.calls == 1 and waits == []


def test_ineligible_providers_are_skipped() -> None:
    small, big = Script("small", "x"), Script("big", "answer")
    fallback, _ = chain(small, big)

    result, used, _ = fallback.run(lambda p: p(), eligible=lambda p: p.name == "big")

    assert used is big and small.calls == 0


def test_when_every_provider_fails_the_attempts_are_reported() -> None:
    fallback, _ = chain(Script("only", ProviderFailure(FailureKind.REFUSED)))

    with pytest.raises(AllProvidersFailed) as failed:
        fallback.run(lambda p: p())

    assert failed.value.attempts == [Attempt("only", "refused", 0)]


def test_the_breaker_skips_a_failing_provider_until_it_cools_down() -> None:
    now = [0.0]
    breaker = CircuitBreaker(threshold=2, cool_down=60, clock=lambda: now[0])
    down = ProviderFailure(FailureKind.TIMEOUT)
    primary = Script("primary", down, down, "recovered")
    backup = Script("backup", "b1", "b2", "b3")
    fallback, _ = chain(primary, backup, breaker=breaker)

    assert fallback.run(lambda p: p())[0] == "b1", "two timeouts open the breaker"
    assert fallback.run(lambda p: p())[0] == "b2", "primary is skipped while open"
    assert primary.calls == 2
    now[0] = 61
    assert fallback.run(lambda p: p())[0] == "recovered", "after the cool-down it is tried"


def test_a_misconfigured_provider_is_skipped_at_once() -> None:
    breaker = CircuitBreaker(threshold=5, clock=lambda: 0.0)
    breaker.record_failure("primary", FailureKind.MISCONFIGURED)

    assert not breaker.allows("primary")


def test_bugs_are_not_swallowed() -> None:
    fallback, _ = chain(Script("primary"), Script("backup", "answer"))

    with pytest.raises(IndexError):
        fallback.run(lambda p: p())


def test_backoff_doubles_and_is_capped() -> None:
    assert [NO_JITTER.wait_before(n) for n in (1, 2, 3, 4, 5)] == [1.0, 2.0, 4.0, 8.0, 8.0]
    assert NO_JITTER.wait_before(1, asked_for=30) == 8.0
