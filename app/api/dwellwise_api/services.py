"""Rules between HTTP and SQL."""

from __future__ import annotations

from . import repositories as repo
from .brief import PROTECTED_ATTRIBUTION
from .names import name_key
from .place import Place
from .schemas import County, SettlementDetail, SettlementSummary, SourceInfo
from .stats import ATTRIBUTION as PLANNING_ATTRIBUTION

ATTRIBUTION = {
    "counties": "County boundaries © Tailte Éireann. CC BY 4.0.",
    "settlements": "Settlement boundaries © Tailte Éireann. CC BY 4.0.",
    "planning": PLANNING_ATTRIBUTION,
    "sac": PROTECTED_ATTRIBUTION,
    "spa": PROTECTED_ATTRIBUTION,
    "nha": PROTECTED_ATTRIBUTION,
}
MIN_KEY_LENGTH = 2  # shorter queries match half the country


def counties(conn) -> list[County]:
    return [County(**row) for row in repo.list_counties(conn)]


def county_settlements(conn, place: Place) -> list[SettlementSummary]:
    """An empty list when the county has no settlements."""
    return [SettlementSummary(**row) for row in repo.county_settlements(conn, place.county)]


def search(conn, query: str, place: Place, limit: int) -> list[SettlementSummary]:
    key = name_key(query)
    if len(key) < MIN_KEY_LENGTH:
        return []
    rows = repo.search_settlements(conn, key, place.county, limit)
    return [SettlementSummary(**row) for row in rows]


def detail(conn, place: Place) -> SettlementDetail | None:
    """None only if the settlement vanished since the gazetteer was loaded."""
    row = repo.get_settlement(conn, place.settlement)
    if row is None:
        return None
    loaded = repo.loaded_sources(conn)
    sources = [
        SourceInfo(name=name, captured_at=loaded[name]["captured_at"], attribution=text)
        for name, text in ATTRIBUTION.items()
        if name in loaded
    ]
    return SettlementDetail(**row, sources=sources)
