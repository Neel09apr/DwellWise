"""Sale prices for Ireland, a county or a town, from the CSO's area statistics.

A town has no price figures of its own. It gets the Eircode routing area that
most of its commencement notices carry; without one, its county's figures. The
choice is stated in ``basis`` so the reader knows which area they are looking at.
"""

from __future__ import annotations

from datetime import date

from . import repositories as repo
from .place import Place
from .schemas import PriceArea, PriceMonth, Prices
from .stats import add_months

ATTRIBUTION = "Central Statistics Office, tables HPM04 and HPM05 (Revenue stamp duty data). CC BY 4.0."
MONTHS = 24


def _area(rows: list[dict]) -> PriceArea:
    by_month: dict[str, dict] = {}
    for r in rows:
        m = by_month.setdefault(r["month"][:7], {"month": r["month"][:7]})
        prefix = "" if r["status"] == "all" else "new_"
        m[prefix + "sales"], m[prefix + "median"] = r["sales"], r["median"]
    months = [
        PriceMonth(**{"sales": None, "median": None, "new_sales": None, "new_median": None, **m})
        for m in sorted(by_month.values(), key=lambda m: m["month"])
    ]
    with_median = [m for m in months if m.median is not None]
    latest = with_median[-1] if with_median else None
    last_year = months[-12:]
    first = rows[0]
    return PriceArea(
        kind=first["kind"],
        code=first["code"],
        name=first["name"],
        latest=latest,
        sales_12_months=sum(m.sales or 0 for m in last_year),
        months=months,
    )


def choose(data: dict) -> tuple[list[tuple[str, str]], str]:
    """Which areas to show, as (kind, code), and why, in words."""
    regions = {(r["code"], r["name"]) for r in data["rows"] if r["kind"] == "region"}
    county = data["county"]
    key = data["key"]
    if key:
        return [("eircode", key["routing_key"])], (
            f"Eircode area {key['routing_key']}: {key['notices']} of the {key['with_eircode']} construction "
            "notices in this town that give an Eircode fall in it. Figures cover the whole routing area, "
            "which is larger than the town."
        )
    if county:
        exact = [c for c, n in regions if n.upper() == county]
        split = sorted(c for c, n in regions if n.upper().startswith(county + " "))
        codes = exact or split
        if codes:
            why = "County figures" if exact else "Figures for each part of the county"
            if data.get("settlement"):
                why += ": no construction notice in this town gives an Eircode to tie it to a smaller area"
            return [("region", c) for c in codes], why + "."
    return [("region", "-")], "Figures for all of Ireland."


def prices(conn, place: Place, today: date) -> Prices:
    """Ireland, a county or a settlement (``Place`` has resolved it, a settlement with its county)."""
    since = add_months(today.replace(day=1), -MONTHS)
    data = repo.price_data(conn, place.county, place.settlement, since)
    picks, basis = choose({**data, "county": place.county, "settlement": place.settlement})
    areas = []
    for kind, code in picks:
        rows = [r for r in data["rows"] if (r["kind"], r["code"]) == (kind, code)]
        if rows:
            areas.append(_area(rows))
    return Prices(
        county=place.asked_county,
        settlement=place.settlement,
        basis=basis,
        captured_at=data["captured_at"],
        attribution=ATTRIBUTION,
        areas=areas,
    )
