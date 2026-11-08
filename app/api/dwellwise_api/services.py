"""Rules between HTTP and SQL."""

from __future__ import annotations

from . import repositories as repo
from .names import name_key
from .schemas import SettlementDetail, SettlementSummary, SourceInfo

ATTRIBUTION = {
    "counties": "County boundaries © Tailte Éireann. CC BY 4.0.",
    "settlements": "Settlement boundaries © Tailte Éireann. CC BY 4.0.",
}
MIN_KEY_LENGTH = 2  # shorter queries match half the country


def search(conn, query: str, county: str | None, limit: int) -> list[SettlementSummary]:
    key = name_key(query)
    if len(key) < MIN_KEY_LENGTH:
        return []
    rows = repo.search_settlements(conn, key, county.strip().upper() if county else None, limit)
    return [SettlementSummary(**row) for row in rows]


def detail(conn, code: str) -> SettlementDetail | None:
    row = repo.get_settlement(conn, code)
    if row is None:
        return None
    loaded = repo.loaded_sources(conn)
    sources = [
        SourceInfo(name=name, captured_at=loaded[name]["captured_at"], attribution=text)
        for name, text in ATTRIBUTION.items()
        if name in loaded
    ]
    return SettlementDetail(**row, sources=sources)
