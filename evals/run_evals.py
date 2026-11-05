"""Score the pipeline against the invented fixtures in evals/fixtures.

    uv run python evals/run_evals.py

Exits with an error when a score drops below its threshold, so CI fails.
"""

import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

from jalada.domain.categories import Purpose
from jalada.pipeline.classifier import Preference
from jalada.pipeline.process import Budget, PipelineResult, run_pipeline

FIXTURES = Path(__file__).parent / "fixtures"
TODAY = date(2026, 11, 5)
THRESHOLDS = {"extraction": 0.90, "classification": 0.80, "verifier rejections": 0.95}


def run_fixture(fixture: dict[str, Any]) -> PipelineResult:
    preferences = {
        key: Preference(p["category"], Purpose(p["purpose"]), p["times_used"])
        for key, p in fixture["preferences"].items()
    }
    return run_pipeline(
        fixture["text"],
        fixture["content_type"],
        preferences,
        is_duplicate=lambda _: bool(fixture["duplicate"]),
        today=TODAY,
        budget=Budget(),
    )


def extraction_matches(result: PipelineResult, expected: dict[str, Any] | None) -> bool:
    if expected is None:
        return result.extraction is None
    if result.extraction is None:
        return False
    found = result.extraction.to_record()
    return all(found.get(name) == value for name, value in expected.items())


def classification_matches(result: PipelineResult, expected: dict[str, Any]) -> bool:
    if result.extraction is None:
        return expected["category"] is None
    found = result.classification
    return found is not None and (found.category, found.purpose) == (
        expected["category"],
        expected["purpose"],
    )


def score() -> dict[str, float]:
    tallies = {name: [0, 0] for name in [*THRESHOLDS, "outcome"]}
    for path in sorted(FIXTURES.glob("*.json")):
        fixture = json.loads(path.read_text())
        expected = fixture["expected"]
        result = run_fixture(fixture)
        checks = {
            "extraction": extraction_matches(result, expected["fields"]),
            "classification": classification_matches(result, expected),
            "outcome": result.kind == expected["kind"] and result.outcome == expected["outcome"],
        }
        if expected["verifier_should_reject"]:
            checks["verifier rejections"] = bool(result.verdict and result.verdict.problems)
        for name, passed in checks.items():
            tallies[name][0] += passed
            tallies[name][1] += 1
            if not passed:
                print(f"  miss  {name:<20} {path.name}")
    return {name: right / total for name, (right, total) in tallies.items() if total}


def main() -> None:
    scores = score()
    failed = False
    for name, value in scores.items():
        threshold = THRESHOLDS.get(name)
        status = "" if threshold is None else ("ok" if value >= threshold else "BELOW")
        failed |= status == "BELOW"
        limit = f"(needs {threshold:.0%})" if threshold else "(reported only)"
        print(f"{name:<20} {value:6.1%}  {limit:<16} {status}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
