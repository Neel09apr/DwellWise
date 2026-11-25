"""Developments on a map: schemes started or applied for, five homes or more, last 12 months."""

from __future__ import annotations

from . import building, stats
from . import repositories as repo
from .schemas import DevelopmentFeature, DevelopmentProperties, Developments, PointGeometry

DAYS = 365


def developments(conn, county: str | None) -> Developments | None:
    """None when the county does not exist. Nothing below ``building.NAMED_FROM`` homes is mapped."""
    name = county.strip().upper() if county else None
    data = repo.development_points(conn, name, building.NAMED_FROM, DAYS)
    if not data["county_known"]:
        return None
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
        features=features,
    )
