"""Homes whose construction has started: commencement notices, per month and recent schemes."""

from __future__ import annotations

from . import repositories as repo
from .months import Months
from .place import Place
from .schemas import CommencementMonth, CommencementStats, HomesCount, Scheme

ATTRIBUTION = "Building Commencement and Completion Data, National Building Control Office. CC BY 4.0."
NAMED_FROM = 5  # the pipeline keeps project names only from this size; list nothing smaller


def commencement_stats(conn, place: Place, months: Months) -> CommencementStats:
    """Ireland, a county or a settlement (``Place`` has resolved it)."""
    data = repo.commencement_data(
        conn, place.asked_county, place.settlement, months.first, months.end, NAMED_FROM
    )

    found = {m["month"]: m for m in data["months"]}
    zero = {"notices": 0, "homes": 0}
    by_month = [
        CommencementMonth(month=m, notices=found.get(m, zero)["notices"], homes=found.get(m, zero)["homes"])
        for m in months.each()
    ]

    return CommencementStats(
        county=place.asked_county,
        settlement=place.settlement,
        from_month=months.from_label,
        to_month=months.to_label,
        captured_at=data["captured_at"],
        newest_submitted=data["newest_submitted"],
        attribution=ATTRIBUTION,
        totals=HomesCount(notices=sum(m.notices for m in by_month), homes=sum(m.homes for m in by_month)),
        last_7_days=HomesCount(**data["last_7_days"]),
        months=by_month,
        recent_schemes=[Scheme(**s) for s in data["recent_schemes"]],
    )
