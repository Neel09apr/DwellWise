"""Planning activity: applications received per month, by their current decision class."""

from __future__ import annotations

from . import repositories as repo
from .months import Months
from .place import Place
from .schemas import ApplicationStats, CountyCounts, DecisionCounts, MonthCounts

CLASSES = ("granted", "refused", "pending", "withdrawn", "other")
ATTRIBUTION = (
    "National Planning Applications, Department of Housing, Local Government and Heritage. CC BY 4.0."
)


def _counts(rows: list[dict]) -> dict:
    counts = dict.fromkeys(CLASSES, 0)
    for r in rows:
        counts[r["decision_class"]] += r["n"]
    return {**counts, "total": sum(counts.values())}


def application_stats(conn, place: Place, residential: bool | None, months: Months) -> ApplicationStats:
    """Ireland or one county (``Place`` has resolved it). Each county in scope gets a row."""
    name = place.county
    data = repo.application_stats_data(conn, name, residential, months.first, months.end)
    rows = data["rows"]
    by_month = [MonthCounts(month=m, **_counts([r for r in rows if r["month"] == m])) for m in months.each()]

    counties = [
        CountyCounts(county=n, **_counts([r for r in rows if r["county"] == n])) for n in place.counties
    ]

    return ApplicationStats(
        county=name,
        residential=residential,
        from_month=months.from_label,
        to_month=months.to_label,
        captured_at=data["captured_at"],
        newest_received=data.get("newest_received"),
        attribution=ATTRIBUTION,
        totals=DecisionCounts(**_counts(rows)),
        months=by_month,
        counties=counties,
    )
