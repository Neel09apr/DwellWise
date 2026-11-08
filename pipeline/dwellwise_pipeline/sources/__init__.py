"""Every source the pipeline knows, by name. Order matters: counties first."""

from . import counties, settlements
from .base import Source

SOURCES: dict[str, Source] = {s.name: s for s in (counties.SOURCE, settlements.SOURCE)}
