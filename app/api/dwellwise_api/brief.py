"""The pre-planning brief for one settlement, section by section.

Sections fill in as their data sources land. Today: planning precedents (F4),
from the national planning applications already placed in each settlement, and
protected sites (F5): SACs, SPAs and NHAs within 5 km of the settlement boundary.
Evidence describes the town, never a site in it; it counts applications, not
schemes, and makes no judgement about any future application.
"""

from __future__ import annotations

from datetime import date

from . import repositories as repo
from .schemas import Brief, DecisionCounts, PrecedentApplication, Precedents, ProtectedSite, ProtectedSites
from .stats import ATTRIBUTION, CLASSES

PRECEDENT_YEARS = 5
RECENT_LIMIT = 10
PENDING_SECTIONS = ["wastewater", "alternatives"]
PROTECTED_RADIUS_M = 5000
NEAR_M = 1000
PROTECTED_ATTRIBUTION = (
    "Protected sites: National Parks and Wildlife Service, Department of Housing, "
    "Local Government and Heritage. CC BY 4.0."
)


def band(distance_m: int) -> str:
    """Touching or overlapping the town, within 1 km, or within 5 km."""
    if distance_m <= 0:
        return "touches"
    return "1km" if distance_m <= NEAR_M else "5km"


def years_before(day: date, years: int) -> date:
    """Same day, `years` earlier; 29 February becomes 28 February."""
    try:
        return day.replace(year=day.year - years)
    except ValueError:
        return day.replace(year=day.year - years, day=28)


def brief(conn, code: str, today: date) -> Brief | None:
    """None when no settlement has this code."""
    since = years_before(today, PRECEDENT_YEARS)
    data = repo.settlement_brief(conn, code, since, RECENT_LIMIT, PROTECTED_RADIUS_M)
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
        protected=ProtectedSites(
            radius_m=PROTECTED_RADIUS_M,
            sites=[ProtectedSite(**s, band=band(s["distance_m"])) for s in data["protected"]],
            captured_at=data["protected_captured_at"],
            attribution=PROTECTED_ATTRIBUTION,
        ),
        pending=PENDING_SECTIONS,
    )
