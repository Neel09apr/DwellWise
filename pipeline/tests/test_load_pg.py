"""Runs against a real PostGIS in CI (DATABASE_URL); skipped where none is available."""

import os
from dataclasses import replace

import pytest

from dwellwise_pipeline.load import LoadError, migrate
from dwellwise_pipeline.raw_store import LocalStore
from dwellwise_pipeline.run import run_source
from dwellwise_pipeline.sources import SOURCES
from dwellwise_pipeline.validate import ValidationError

pytestmark = pytest.mark.integration
psycopg = pytest.importorskip("psycopg")
URL = os.environ.get("DATABASE_URL")

# The real minimums (26 counties, 800 settlements) are lowered for small fixtures.
COUNTIES = replace(SOURCES["counties"], min_rows=1)
SETTLEMENTS = replace(SOURCES["settlements"], min_rows=1)
PLANNING = replace(SOURCES["planning"], min_rows=1)


@pytest.fixture
def conn():
    if not URL:
        pytest.skip("DATABASE_URL not set")
    with psycopg.connect(URL, autocommit=True) as c:
        c.execute("drop schema if exists dw cascade")
        migrate(c)
        yield c


def test_settlements_get_the_containing_or_nearest_county(conn, tmp_path, counties, settlements):
    store = LocalStore(tmp_path)
    run_source(COUNTIES, store, conn, fetch=lambda *a: counties)
    result = run_source(SETTLEMENTS, store, conn, fetch=lambda *a: settlements)

    got = dict(conn.execute("select code, county from dw.settlement order by code").fetchall())
    assert got == {"1001": "CORK", "1002": "KERRY"}
    assert result.detail == {"county_by_nearest": 1}
    srid = conn.execute("select distinct ST_SRID(boundary) from dw.settlement").fetchall()
    assert srid == [(2157,)]


def test_settlements_refuse_to_load_without_counties(conn, tmp_path, settlements):
    with pytest.raises(LoadError, match="load counties before settlements"):
        run_source(SETTLEMENTS, LocalStore(tmp_path), conn, fetch=lambda *a: settlements)
    status = conn.execute("select status from dw.snapshot").fetchall()
    assert status == [("failed",)]


def test_a_rejected_run_leaves_yesterdays_data_in_place(conn, tmp_path, counties):
    store = LocalStore(tmp_path)
    run_source(COUNTIES, store, conn, fetch=lambda *a: counties)

    bad = {"type": "FeatureCollection", "features": [dict(counties["features"][0], geometry=None)]}
    with pytest.raises(ValidationError):
        run_source(COUNTIES, store, conn, fetch=lambda *a: bad)

    names = [r[0] for r in conn.execute("select name from dw.county order by name").fetchall()]
    assert names == ["CORK", "KERRY"]
    statuses = [r[0] for r in conn.execute("select status from dw.snapshot order by fetched_at").fetchall()]
    assert statuses == ["loaded", "rejected"]


def application(number: str, lon: float, lat: float, **props) -> dict:
    base = {
        "PlanningAuthority": "Cork County Council",
        "ApplicationNumber": number,
        "ReceivedDate": 1752451200000,
        "DecisionDate": None,
        "WithdrawnDate": None,
        "Decision": "CONDITIONAL",
        "ApplicationStatus": "",
        "NumResidentialUnits": 2,
        "OneOffHouse": "",
    }
    return {
        "type": "Feature",
        "properties": {**base, **props},
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
    }


def test_planning_loads_with_settlement_classes_and_no_duplicates(conn, tmp_path, counties, settlements):
    store = LocalStore(tmp_path)
    run_source(COUNTIES, store, conn, fetch=lambda *a: counties)
    run_source(SETTLEMENTS, store, conn, fetch=lambda *a: settlements)
    apps = {
        "type": "FeatureCollection",
        "features": [
            application("A1", -8.55, 51.95),  # inside settlement 1001
            application("A2", -8.2, 52.1, Decision="Something new"),  # open country, unknown wording
            application("A1", -8.55, 51.95, ReceivedDate=1700000000000, Decision="REFUSED"),  # older copy
        ],
    }
    result = run_source(PLANNING, store, conn, fetch=lambda *a: apps)

    got = conn.execute(
        "select application_number, decision_class, settlement, county, received::text "
        "from dw.planning_application order by application_number"
    ).fetchall()
    assert got == [
        ("A1", "granted", "1001", "CORK", "2025-07-14"),
        ("A2", "other", None, "CORK", "2025-07-14"),
    ]
    assert result.detail == {"duplicates_dropped": 1, "decisions_unrecognised": 1}
    assert conn.execute("select distinct ST_SRID(location) from dw.planning_application").fetchall() == [
        (2157,)
    ]


def test_planning_refuses_to_load_without_settlements(conn, tmp_path):
    apps = {"type": "FeatureCollection", "features": [application("A1", -8.55, 51.95)]}
    with pytest.raises(LoadError, match="load settlements before planning"):
        run_source(PLANNING, LocalStore(tmp_path), conn, fetch=lambda *a: apps)


def site(code: str, name: str, west: float) -> dict:
    return {
        "type": "Feature",
        "properties": {"SITECODE": code, "SITE_NAME": name, "URL": f"https://www.npws.ie/x/{code}"},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[west, 52.0], [west + 0.01, 52.0], [west + 0.01, 52.01], [west, 52.0]]],
        },
    }


def test_protected_sites_merge_split_sites_and_replace_only_their_designation(conn, tmp_path):
    store = LocalStore(tmp_path)
    sac = replace(SOURCES["sac"], min_rows=1)
    nha = replace(SOURCES["nha"], min_rows=1)
    split = [site("000001", "Bog SAC", -8.5), site("000001", "Bog SAC", -8.4)]  # one site, two features
    result = run_source(sac, store, conn, fetch=lambda *a: {"features": split})
    run_source(nha, store, conn, fetch=lambda *a: {"features": [site("000001", "Bog NHA", -8.5)]})
    # A new SAC edition replaces the SACs and leaves the NHA alone. Two features, so the
    # row count stays within the drift check of the first run's two.
    edition = [site("000002", "Fen SAC", -8.3), site("000003", "Moss SAC", -8.2)]
    run_source(sac, store, conn, fetch=lambda *a: {"features": edition})

    got = conn.execute(
        "select designation, site_code, name, ST_NumGeometries(boundary), ST_SRID(boundary) "
        "from dw.protected_site order by designation, site_code"
    ).fetchall()
    assert got == [
        ("NHA", "000001", "Bog NHA", 1, 2157),
        ("SAC", "000002", "Fen SAC", 1, 2157),
        ("SAC", "000003", "Moss SAC", 1, 2157),
    ]
    assert result.detail == {"features_merged": 1}


def test_commencements_are_placed_in_their_settlement(conn, tmp_path, counties, settlements):
    from dwellwise_pipeline.sources.commencements import NAMED_FROM

    store = LocalStore(tmp_path)
    run_source(COUNTIES, store, conn, fetch=lambda *a: counties)
    run_source(SETTLEMENTS, store, conn, fetch=lambda *a: settlements)

    def notice(number: str, lng: float, homes: int) -> dict:
        return {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lng, 51.95]},
            "properties": {
                "notice_number": number, "local_authority": "Cork County Council", "submitted": "2026-11-23",
                "commenced": "2026-12-01", "expected_end": None, "homes": homes, "scheme_homes": homes,
                "planning_ref": "23/68", "project_name": "Scheme" if homes >= NAMED_FROM else None,
                "homes_completed": 0,
            },
        }  # fmt: skip

    notices = {"type": "FeatureCollection", "features": [notice("CN1", -8.55, 9), notice("CN2", -8.2, 1)]}
    result = run_source(replace(SOURCES["commencements"], min_rows=1), store, conn, fetch=lambda *a: notices)

    got = conn.execute(
        "select notice_number, county, settlement, homes from dw.commencement order by 1"
    ).fetchall()
    assert got == [("CN1", "CORK", "1001", 9), ("CN2", "CORK", None, 1)]
    assert result.detail == {"in_a_settlement": 1}
