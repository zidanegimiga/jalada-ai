"""Score a real model on reading invented receipt photos, with its cost and time.

    JALADA_MODEL_PROVIDERS='{"gemini": {"api_key": "..."}}' \\
        uv run python evals/run_photo_evals.py --model gemini-3.5-flash-lite

Each file in evals/photos/ is an invented receipt as lines of text. It is drawn as a phone
photo, the way the tests draw one, and given to the model alone, with no OCR text, so the
score is the model's own reading. One photo is too blurred to read: as in production, the
photo check stops it before the model, and no amount may come out of it.

For choosing a provider (AI-09) and comparing models (AI-10). Not part of CI: a recorded reply
cannot say which model reads photos best.
"""

import argparse
import json
import sys
import time
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api" / "tests"))

from live_models import real_model  # noqa: E402
from samples import make_receipt_photo  # noqa: E402

from jalada.modules.pipeline.adapters.text.photo_check import PillowPhotoCheck  # noqa: E402
from jalada.modules.pipeline.domain.model import ImageInput  # noqa: E402
from jalada.modules.pipeline.domain.process import run_pipeline  # noqa: E402
from jalada.modules.pipeline.domain.run_types import Budget, EvidenceInput  # noqa: E402

PHOTOS = Path(__file__).parent / "photos"
TODAY = date(2026, 11, 18)
FIELDS = ("amount_cents", "occurred_on", "direction", "counterparty")


def score_photo(photo: dict[str, Any], model_name: str) -> dict[str, Any]:
    image = make_receipt_photo(photo["lines"], noise=photo["blur"])
    started = time.perf_counter()
    # The same check production makes: a photo nobody could read gets no model at all.
    readable = PillowPhotoCheck().problem(image) is None
    result = run_pipeline(
        EvidenceInput(None, "image/jpeg", ImageInput(image, "image/jpeg")),
        {},
        is_duplicate=lambda _: False,
        today=TODAY,
        budget=Budget(),
        model=real_model(model_name) if readable else None,
    )
    seconds = time.perf_counter() - started
    found = result.extraction.to_record() if result.extraction else {}
    expected = photo["expected"]["fields"]
    if expected is None:
        # Unreadable: right only if no amount was made up.
        right = {"no amount made up": found.get("amount_cents") is None}
    else:
        right = {name: _same(found.get(name), expected[name]) for name in FIELDS}
    return {"right": right, "cost": result.usage.cost_usd, "seconds": seconds}


def _same(found: Any, expected: Any) -> bool:
    if isinstance(expected, str) and isinstance(found, str):
        return " ".join(found.casefold().split()) == " ".join(expected.casefold().split())
    return bool(found == expected)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", required=True, help="a catalogue name")
    arguments = parser.parse_args()
    fields_right = fields_total = 0
    cost, seconds = Decimal(0), 0.0
    for path in sorted(PHOTOS.glob("*.json")):
        photo = json.loads(path.read_text())
        scored = score_photo(photo, arguments.model)
        missed = [name for name, ok in scored["right"].items() if not ok]
        fields_right += len(scored["right"]) - len(missed)
        fields_total += len(scored["right"])
        cost += scored["cost"]
        seconds += scored["seconds"]
        status = "ok" if not missed else "missed " + ", ".join(missed)
        print(f"  {path.stem:<28} {scored['seconds']:5.1f}s  {status}")
    count = len(list(PHOTOS.glob("*.json")))
    print(f"fields right {fields_right / fields_total:6.1%}  ({fields_right} of {fields_total})")
    print(f"cost         ${cost:.4f} for {count} photos, ${cost / count:.5f} each")
    print(f"time         {seconds / count:.1f}s a photo on average")


if __name__ == "__main__":
    main()
