"""The development map without a database: one round trip, GeoJSON shape, unknown counties refused."""

from datetime import date

from dwellwise_api.developments import developments
from dwellwise_api.main import SECURITY_HEADERS

from .test_stats import CountingConn

POINT = {
    "kind": "started", "label": "Bunclody Woods", "authority": "Carlow County Council", "homes": 9,
    "day": date(2026, 12, 1), "settlement": "Bunclody", "status": None, "reference": "23/68",
    "lng": "-6.6621", "lat": "52.6595",
}  # fmt: skip


def test_points_become_geojson_in_one_round_trip():
    conn = CountingConn({"county_known": True, "points": [POINT]})
    found = developments(conn, None)
    assert conn.queries == 1
    body = found.model_dump()
    assert body["type"] == "FeatureCollection" and body["min_homes"] == 5
    (feature,) = body["features"]
    assert feature["geometry"] == {"type": "Point", "coordinates": [-6.6621, 52.6595]}
    assert feature["properties"]["label"] == "Bunclody Woods"
    assert "lng" not in feature["properties"]


def test_an_unknown_county_is_none():
    assert developments(CountingConn({"county_known": False, "points": []}), "atlantis") is None


def test_the_page_may_load_map_tiles_from_openfreemap_and_nowhere_else():
    csp = SECURITY_HEADERS["Content-Security-Policy"]
    assert "connect-src 'self' https://tiles.openfreemap.org;" in csp
    assert "worker-src 'self'" in csp and "blob:" not in csp.split("worker-src")[1].split(";")[0]
    assert "script-src" not in csp  # scripts stay on default-src 'self'
