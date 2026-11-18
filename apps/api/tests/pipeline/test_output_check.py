from jalada.modules.pipeline.adapters.models.output_check import problems
from jalada.modules.pipeline.domain.prompts import EXTRACTION_SCHEMA

GOOD = {
    "kind": "receipt",
    "occurred_on": "2026-11-04",
    "direction": "out",
    "amount_ksh": "1,250.00",
    "counterparty": "SAMPLE SHOP",
    "confidence": 0.9,
    "readable": True,
}


def test_a_matching_answer_has_no_problems() -> None:
    assert problems(GOOD, EXTRACTION_SCHEMA) == []
    assert problems({**GOOD, "direction": None, "counterparty": None}, EXTRACTION_SCHEMA) == []


def test_missing_fields_wrong_types_and_unknown_values_are_named() -> None:
    answer = {**GOOD, "kind": "lottery", "confidence": "high"}
    del answer["amount_ksh"]

    assert sorted(problems(answer, EXTRACTION_SCHEMA)) == [
        "answer.amount_ksh is missing",
        "answer.confidence has the wrong type",
        "answer.kind is not one of the allowed values",
    ]


def test_true_is_not_a_number() -> None:
    assert problems({**GOOD, "confidence": True}, EXTRACTION_SCHEMA) == [
        "answer.confidence has the wrong type"
    ]


def test_an_answer_that_does_not_say_whether_it_could_read_is_refused() -> None:
    answer = dict(GOOD)
    del answer["readable"]

    assert problems(answer, EXTRACTION_SCHEMA) == ["answer.readable is missing"]
