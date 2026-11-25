"""Every source the pipeline knows, by name: the only place a source is declared.

The order is the run order, the dependency order (each source comes after the
sources in its ``after``) and the order the API lists sources in. Each run
registers its source in ``dw.source``; the API reads that table.
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
