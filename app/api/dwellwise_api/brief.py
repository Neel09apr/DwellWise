"""The pre-planning brief for one settlement, section by section.

Sections fill in as their data sources land. Today: planning precedents (F4),
from the national planning applications already placed in each settlement.
Evidence describes the town, never a site in it; it counts applications, not
schemes, and makes no judgement about any future application.
"""

from __future__ import annotations

from datetime import date

from . import repositories as repo
from .schemas import Brief, DecisionCounts, PrecedentApplication, Precedents
from .stats import ATTRIBUTION, CLASSES

PRECEDENT_YEARS = 5
RECENT_LIMIT = 10
PENDING_SECTIONS = ["wastewater", "protected", "alternatives"]


def years_before(day: date, years: int) -> date:
    """Same day, `years` earlier; 29 February becomes 28 February."""
    try:
        return day.replace(year=day.year - years)
    except ValueError:
        return day.replace(year=day.year - years, day=28)


def brief(conn, code: str, today: date) -> Brief | None:
    """None when no settlement has this code."""
    since = years_before(today, PRECEDENT_YEARS)
    data = repo.settlement_precedents(conn, code, since, RECENT_LIMIT)
    if not data["found"]:
        return None
    counts = {c: int(data["residential"].get(c, 0)) for c in CLASSES}
    return Brief(
        code=code,
        precedents=Precedents(
            since=since,
            years=PRECEDENT_YEARS,
            residential=DecisionCounts(**counts, total=sum(counts.values())),
            all_applications=data["all_total"],
            recent=[PrecedentApplication(**r) for r in data["recent"]],
            captured_at=data["captured_at"],
            attribution=ATTRIBUTION,
        ),
        pending=PENDING_SECTIONS,
    )
