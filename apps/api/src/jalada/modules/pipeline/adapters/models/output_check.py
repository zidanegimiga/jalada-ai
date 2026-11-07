"""Checks a model's JSON against the schema it was asked for, so a wrong answer is caught
and the next model tried, instead of a half-right answer reaching the ledger.

Covers what our schemas use: objects, required fields, types (including lists of types
such as ["string", "null"]) and enums.
"""

from typing import Any

TYPES: dict[str, tuple[type, ...]] = {
    "string": (str,),
    "number": (int, float),
    "integer": (int,),
    "boolean": (bool,),
    "null": (type(None),),
    "object": (dict,),
    "array": (list,),
}


def problems(data: Any, schema: dict[str, Any], path: str = "answer") -> list[str]:
    """What is wrong with `data`, field by field. Empty when it matches."""
    found = _type_problem(data, schema, path)
    if found:
        return [found]
    if "enum" in schema and data not in schema["enum"]:
        return [f"{path} is not one of the allowed values"]
    if isinstance(data, dict):
        return _object_problems(data, schema, path)
    return []


def _type_problem(data: Any, schema: dict[str, Any], path: str) -> str | None:
    expected = schema.get("type")
    if expected is None:
        return None
    names = expected if isinstance(expected, list) else [expected]
    # bool is an int in Python, but never a number in JSON.
    if isinstance(data, bool) and "boolean" not in names:
        return f"{path} has the wrong type"
    if any(isinstance(data, TYPES.get(name, ())) for name in names):
        return None
    return f"{path} has the wrong type"


def _object_problems(data: dict[str, Any], schema: dict[str, Any], path: str) -> list[str]:
    found = [f"{path}.{key} is missing" for key in schema.get("required", []) if key not in data]
    for key, rule in schema.get("properties", {}).items():
        if key in data:
            found += problems(data[key], rule, f"{path}.{key}")
    return found
