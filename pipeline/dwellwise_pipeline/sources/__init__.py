"""Every source the pipeline knows, by name. Order matters: counties, settlements, then planning.

Protected sites depend on nothing; the brief relates them to settlements at query time.
Commencement notices, like planning, are placed in settlements, so they come after them.
"""

from . import commencements, counties, planning, prices, protected, settlements
from .base import Source

SOURCES: dict[str, Source] = {
    s.name: s
    for s in (
        counties.SOURCE,
        settlements.SOURCE,
        planning.SOURCE,
        protected.SAC,
        protected.SPA,
        protected.NHA,
        commencements.SOURCE,
        prices.SOURCE,
    )
}
