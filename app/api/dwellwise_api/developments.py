"""Developments on a map: schemes started or applied for, five homes or more, last 12 months."""

from __future__ import annotations

from . import building, stats
from . import repositories as repo
from .place import Place
from .schemas import DevelopmentFeature, DevelopmentProperties, Developments, PointGeometry, UnitReporting

DAYS = 365
SPARSE_BELOW = 10  # percent of applications stating units, under which a council is named


def developments(conn, place: Place) -> Developments:
    """Ireland or one county (``Place`` has resolved it). Nothing below ``building.NAMED_FROM`` homes."""
    name = place.county
    data = repo.development_points(conn, name, building.NAMED_FROM, DAYS, SPARSE_BELOW)
    features = [
        DevelopmentFeature(
            geometry=PointGeometry(coordinates=[float(p["lng"]), float(p["lat"])]),
            properties=DevelopmentProperties(**{k: v for k, v in p.items() if k not in ("lng", "lat")}),
        )
        for p in data["points"]
    ]
    return Developments(
        county=name,
        min_homes=building.NAMED_FROM,
        attribution=[building.ATTRIBUTION, stats.ATTRIBUTION],
        sparse_units=[UnitReporting(**u) for u in data["sparse_units"]],
        features=features,
    )
