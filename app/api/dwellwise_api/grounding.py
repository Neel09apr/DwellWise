"""Every number in an answer must come from the data: a tool result from the same run, or the question.

Numbers are compared by value after removing thousands separators, so
"€420,000" matches 420000 and "12.50" matches 12.5. A derived number (a sum,
a rounding, "420k") is not in the data and fails the check.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")


def numbers(text: str) -> set[Decimal]:
    found = set()
    for match in NUMBER.findall(text):
        try:
            found.add(Decimal(match.replace(",", "")).normalize())
        except InvalidOperation:
            continue
    return found


def ungrounded(answer: str, sources: list[str]) -> set[Decimal]:
    """The numbers in the answer that no source contains; empty means the answer may be shown."""
    known = set().union(*(numbers(s) for s in sources)) if sources else set()
    return numbers(answer) - known
