"""Which models a question goes to: a fast, cheap chain for lookups, a stronger one for the rest.

A rule, not a model: it costs nothing, gives the same answer every time, and is easy to read.
Most questions are single lookups ("How much did I pay KPLC?"); comparisons, trends, reasons
and several questions at once need more steps and a model that plans better.
"""

import re
from enum import StrEnum

# Longer than this, a question usually asks more than one thing.
LONG_QUESTION = 160

DEEP_SIGNS = re.compile(
    r"\b(compare|compared|comparison|versus|vs|trend|trends|why|difference|differ|"
    r"each month|every month|month by month|breakdown|average|grew|growth|"
    r"over the (last|past)|between .+ and)\b",
    re.I,
)


class Route(StrEnum):
    FAST = "fast"
    DEEP = "deep"


def route_for(question: str) -> Route:
    text = " ".join(question.split())
    if len(text) > LONG_QUESTION or text.count("?") > 1 or DEEP_SIGNS.search(text):
        return Route.DEEP
    return Route.FAST
