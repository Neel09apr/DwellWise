"""Every source the pipeline knows, by name. Order matters: counties, settlements, then planning."""

from . import counties, planning, settlements
from .base import Source

SOURCES: dict[str, Source] = {s.name: s for s in (counties.SOURCE, settlements.SOURCE, planning.SOURCE)}
