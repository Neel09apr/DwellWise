"""Every number in an answer must come from the data: a tool result from the same run, or the question.

Numbers are compared by value after removing thousands separators, so
"€420,000" matches 420000 and "12.50" matches 12.5. A derived number (a sum,
a rounding, "420k") is not in the data and fails the check.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")
# No-break, narrow and thin spaces between digit groups are thousands separators (U+00A0, U+202F,
# U+2009, as in 420<U+202F>000). An ordinary space is not: "8 110" must stay two numbers.
GROUP_SPACE = re.compile(r"(?<=\d)[\u00a0\u202f\u2009](?=\d{3}(?!\d))")


def numbers(text: str) -> set[Decimal]:
    found = set()
    for match in NUMBER.findall(GROUP_SPACE.sub("", text)):
        try:
            found.add(Decimal(match.replace(",", "")).normalize())
        except InvalidOperation:
            continue
    return found


def ungrounded(answer: str, sources: list[str]) -> set[Decimal]:
    """The numbers in the answer that no source contains; empty means the answer may be shown."""
    known = set().union(*(numbers(s) for s in sources)) if sources else set()
    return numbers(answer) - known
