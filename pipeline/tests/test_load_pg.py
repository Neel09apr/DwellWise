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
