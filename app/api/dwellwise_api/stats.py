"""Planning activity: applications received per month, by their current decision class."""

from __future__ import annotations

from datetime import date

from . import repositories as repo
from .schemas import ApplicationStats, CountyCounts, DecisionCounts, MonthCounts

CLASSES = ("granted", "refused", "pending", "withdrawn", "other")
DEFAULT_MONTHS = 12
MAX_MONTHS = 120
ATTRIBUTION = (
    "National Planning Applications, Department of Housing, Local Government and Heritage. CC BY 4.0."
)


class RangeError(ValueError):
    """The requested months make no sense, or span too long."""


def parse_month(text: str) -> date:
    year, month = text.split("-")
    return date(int(year), int(month), 1)


def add_months(day: date, n: int) -> date:
    index = day.year * 12 + day.month - 1 + n
    return date(index // 12, index % 12 + 1, 1)


def month_range(start: str | None, end: str | None, today: date) -> tuple[date, date]:
    """First and last month, inclusive. Defaults to the last 12 months up to today's."""
    last = parse_month(end) if end else today.replace(day=1)
    first = parse_month(start) if start else add_months(last, -(DEFAULT_MONTHS - 1))
    if first > last:
        raise RangeError("from must not be after to.")
    if (last.year - first.year) * 12 + last.month - first.month + 1 > MAX_MONTHS:
        raise RangeError(f"The range may span at most {MAX_MONTHS} months.")
    return first, last


def _counts(rows: list[dict]) -> dict:
    counts = dict.fromkeys(CLASSES, 0)
    for r in rows:
        counts[r["decision_class"]] += r["n"]
    return {**counts, "total": sum(counts.values())}


def application_stats(
    conn, county: str | None, residential: bool | None, start: str | None, end: str | None, today: date
) -> ApplicationStats | None:
    """None when the county does not exist."""
    first, last = month_range(start, end, today)
    name = county.strip().upper() if county else None
    data = repo.application_stats_data(conn, name, residential, first, add_months(last, 1))
    if name and name not in data["counties"]:
        return None
    rows = data["rows"]

    months, day = [], first
    while day <= last:
        months.append(MonthCounts(month=f"{day:%Y-%m}", **_counts([r for r in rows if r["month"] == day])))
        day = add_months(day, 1)

    names = [name] if name else data["counties"]
    counties = [CountyCounts(county=n, **_counts([r for r in rows if r["county"] == n])) for n in names]

    return ApplicationStats(
        county=name,
        residential=residential,
        from_month=f"{first:%Y-%m}",
        to_month=f"{last:%Y-%m}",
        captured_at=data["captured_at"],
        attribution=ATTRIBUTION,
        totals=DecisionCounts(**_counts(rows)),
        months=months,
        counties=counties,
    )
