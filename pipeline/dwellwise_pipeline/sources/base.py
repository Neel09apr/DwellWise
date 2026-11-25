from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class Source:
    name: str
    required_fields: tuple[str, ...]
    min_rows: int
    table: str
    attribution: str
    transform: Callable[[dict], list[dict]]
    fetch: Callable[[], dict]  # reads the whole source: an arcgis.Layer, or the source's own reader
    check: Callable[[dict], list[str]] | None = None  # extra problems that reject a run
    geometry: bool = True  # statistics tables (prices) have none
    after: tuple[str, ...] = ()  # sources whose rows this source's loader needs; SOURCES lists them earlier
