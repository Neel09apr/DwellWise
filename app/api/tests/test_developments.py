"""The development map without a database: one round trip, GeoJSON shape, unknown counties refused."""

from datetime import date

from dwellwise_api.developments import developments
from dwellwise_api.main import SECURITY_HEADERS
from dwellwise_api.place import Place

from .test_stats import CountingConn

POINT = {
    "kind": "started", "label": "Bunclody Woods", "authority": "Carlow County Council", "homes": 9,
    "day": date(2026, 12, 1), "settlement": "Bunclody", "status": None, "reference": "23/68",
    "lng": "-6.6621", "lat": "52.6595",
}  # fmt: skip


def test_points_become_geojson_in_one_round_trip():
    sparse = [{"authority": "Cork County Council", "share": 0}]
    conn = CountingConn({"points": [POINT], "sparse_units": sparse})
    found = developments(conn, Place())
    assert conn.queries == 1
    body = found.model_dump()
    assert body["type"] == "FeatureCollection" and body["min_homes"] == 5
    (feature,) = body["features"]
    assert feature["geometry"] == {"type": "Point", "coordinates": [-6.6621, 52.6595]}
    assert feature["properties"]["label"] == "Bunclody Woods"
    assert "lng" not in feature["properties"]
    assert body["sparse_units"] == [{"authority": "Cork County Council", "share": 0}]


def test_the_page_may_load_map_tiles_from_openfreemap_and_nowhere_else():
    csp = SECURITY_HEADERS["Content-Security-Policy"]
    assert "connect-src 'self' https://tiles.openfreemap.org;" in csp
    assert "worker-src 'self'" in csp and "blob:" not in csp.split("worker-src")[1].split(";")[0]
    assert "script-src" not in csp  # scripts stay on default-src 'self'


def test_the_typeface_is_self_hosted_and_no_third_party_may_serve_styles_or_fonts():
    import mimetypes

    csp = SECURITY_HEADERS["Content-Security-Policy"]
    assert "font-src 'self';" in csp and "style-src 'self';" in csp
    assert "googleapis" not in csp and "gstatic" not in csp
    assert mimetypes.guess_type("archivo.woff2")[0] == "font/woff2"
