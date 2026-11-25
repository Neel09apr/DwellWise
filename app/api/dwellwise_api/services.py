"""Rules between HTTP and SQL."""

from __future__ import annotations

from . import repositories as repo
from .names import name_key
from .place import Place
from .schemas import County, SettlementDetail, SettlementSummary, SourceInfo

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
    sources = [  # every loaded source, in the pipeline's order, with its own attribution
        SourceInfo(name=s["name"], captured_at=s["captured_at"], attribution=s["attribution"])
        for s in repo.registered_sources(conn)
        if s["captured_at"] is not None
    ]
    return SettlementDetail(**row, sources=sources)
