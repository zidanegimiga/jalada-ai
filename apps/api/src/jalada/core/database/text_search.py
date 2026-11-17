"""Matching what a person types against stored text."""


def contains_pattern(text: str) -> str:
    """A LIKE pattern for `text` anywhere in a value. The person's own % and _ are escaped
    with a backslash, so they match themselves instead of standing for other characters."""
    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"
