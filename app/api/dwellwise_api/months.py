"""Months: the whole months a request asks for with ``from`` and ``to`` (YYYY-MM), checked once.

Endpoints take a ``MonthRange``: a bad month or range ends the request with a
422 before any feature code runs, and features get a ``Months`` they can trust.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date
from typing import Annotated

from fastapi import Depends, HTTPException, Query

DEFAULT_MONTHS = 12
MAX_MONTHS = 120
PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"


class RangeError(ValueError):
    """The requested months make no sense, or span too long."""


def add_months(day: date, n: int) -> date:
    """The first day of the month ``n`` months from ``day``'s."""
    index = day.year * 12 + day.month - 1 + n
    return date(index // 12, index % 12 + 1, 1)


def _parse(text: str) -> date:
    year, month = text.split("-")
    return date(int(year), int(month), 1)


@dataclass(frozen=True)
class Months:
    first: date  # first day of the first month
    last: date  # first day of the last month (inclusive)

    @classmethod
    def between(cls, start: str | None, end: str | None, today: date) -> Months:
        """``start`` to ``end``, inclusive. Defaults to the last 12 months up to today's."""
        last = _parse(end) if end else today.replace(day=1)
        first = _parse(start) if start else add_months(last, -(DEFAULT_MONTHS - 1))
        if first > last:
            raise RangeError("from must not be after to.")
        if (last.year - first.year) * 12 + last.month - first.month + 1 > MAX_MONTHS:
            raise RangeError(f"The range may span at most {MAX_MONTHS} months.")
        return cls(first, last)

    @property
    def end(self) -> date:
        """The day after the range: queries read ``[first, end)``."""
        return add_months(self.last, 1)

    @property
    def from_label(self) -> str:
        return f"{self.first:%Y-%m}"

    @property
    def to_label(self) -> str:
        return f"{self.last:%Y-%m}"

    def each(self) -> Iterator[str]:
        """Every month in the range as YYYY-MM, oldest first."""
        day = self.first
        while day <= self.last:
            yield f"{day:%Y-%m}"
            day = add_months(day, 1)


def month_range(
    start: Annotated[
        str | None, Query(alias="from", pattern=PATTERN, description="First month, YYYY-MM")
    ] = None,
    end: Annotated[str | None, Query(alias="to", pattern=PATTERN, description="Last month, YYYY-MM")] = None,
) -> Months:
    """FastAPI dependency: the months asked for, or a 422 that ends the request."""
    try:
        return Months.between(start, end, date.today())
    except RangeError as exc:
        raise HTTPException(422, str(exc)) from exc


MonthRange = Annotated[Months, Depends(month_range)]
