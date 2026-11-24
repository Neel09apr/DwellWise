"""Homes whose construction has started: commencement notices, per month and recent schemes."""

from __future__ import annotations

from datetime import date

from . import repositories as repo
from .schemas import CommencementMonth, CommencementStats, HomesCount, Scheme
from .stats import add_months, month_range

ATTRIBUTION = "Building Commencement and Completion Data, National Building Control Office. CC BY 4.0."
NAMED_FROM = 5  # the pipeline keeps project names only from this size; list nothing smaller


def commencement_stats(
    conn, county: str | None, settlement: str | None, start: str | None, end: str | None, today: date
) -> CommencementStats | None:
    """None when the county or settlement does not exist."""
    first, last = month_range(start, end, today)
    name = county.strip().upper() if county else None
    data = repo.commencement_data(conn, name, settlement, first, add_months(last, 1), NAMED_FROM)
    if not (data["county_known"] and data["settlement_known"]):
        return None

    found = {m["month"]: m for m in data["months"]}
    months, day = [], first
    while day <= last:
        m = found.get(f"{day:%Y-%m}", {"notices": 0, "homes": 0})
        months.append(CommencementMonth(month=f"{day:%Y-%m}", notices=m["notices"], homes=m["homes"]))
        day = add_months(day, 1)

    return CommencementStats(
        county=name,
        settlement=settlement,
        from_month=f"{first:%Y-%m}",
        to_month=f"{last:%Y-%m}",
        captured_at=data["captured_at"],
        newest_submitted=data["newest_submitted"],
        attribution=ATTRIBUTION,
        totals=HomesCount(notices=sum(m.notices for m in months), homes=sum(m.homes for m in months)),
        last_7_days=HomesCount(**data["last_7_days"]),
        months=months,
        recent_schemes=[Scheme(**s) for s in data["recent_schemes"]],
    )
