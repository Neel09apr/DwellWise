"""A county's towns side by side, for comparing places for a scheme (M13).

Code ranks; the assistant only explains. Each column comes from a loaded source,
and the list is sorted by one stated column, never a weighted score: a score
would be a judgement presented as a fact. Nothing here says whether permission
would be granted, and wastewater capacity is not among the columns because
DwellWise does not hold it (DESIGN.md section 6).
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from . import repositories as repo
from .brief import NEAR_M, PRECEDENT_YEARS, PROTECTED_ATTRIBUTION, years_before
from .building import ATTRIBUTION as COMMENCEMENT_ATTRIBUTION
from .months import add_months
from .place import Place
from .prices import ATTRIBUTION as PRICE_ATTRIBUTION
from .schemas import Shortlist, ShortlistTown
from .stats import ATTRIBUTION as PLANNING_ATTRIBUTION

TOP = 5
PRICE_MONTHS = 24
Key = Callable[[ShortlistTown], tuple]
SORTS: dict[str, tuple[str, Key]] = {  # name -> (in words, key; lower sorts first)
    "started": ("homes started in the last 12 months, most first",
                lambda t: (-t.homes_started, -t.granted, t.name)),
    "granted": ("residential applications granted, most first",
                lambda t: (-t.granted, -t.homes_started, t.name)),
    "protected": ("protected sites within 1 km, fewest first",
                  lambda t: (t.protected_within_1km, -t.homes_started, t.name)),
    "price": ("median sale price of the Eircode area, lowest first; towns without one last",
              lambda t: (t.median_price is None, t.median_price or 0, t.name)),
}  # fmt: skip


def rank(towns: list[ShortlistTown], sort: str) -> list[ShortlistTown]:
    return sorted(towns, key=SORTS[sort][1])[:TOP]


def shortlist(conn, place: Place, sort: str, today: date) -> Shortlist:
    """``place`` is a resolved county; ``sort`` one of ``SORTS``."""
    since = years_before(today, PRECEDENT_YEARS)
    month = today.replace(day=1)
    started_from = add_months(month, -11)
    rows = repo.shortlist_rows(
        conn,
        place.county,
        since,
        started_from,
        add_months(month, 1),
        NEAR_M,
        add_months(month, -PRICE_MONTHS),
    )
    towns = [ShortlistTown(**r) for r in rows]
    return Shortlist(
        county=place.county,
        sort=sort,
        sorted_by=SORTS[sort][0],
        towns_in_county=len(towns),
        applications_since=since,
        started_since=started_from.isoformat()[:7],
        towns=rank(towns, sort),
        note=(
            "Evidence about towns, not a judgement on any site or application. Wastewater treatment "
            "capacity is not in DwellWise's data: each town's brief links to the county's register. "
            "Prices cover the whole Eircode routing area, which is larger than the town."
        ),
        attribution=[
            PLANNING_ATTRIBUTION,
            COMMENCEMENT_ATTRIBUTION,
            PROTECTED_ATTRIBUTION,
            PRICE_ATTRIBUTION,
        ],
    )
