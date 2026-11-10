"""Runs against a real PostGIS in CI (DATABASE_URL); skipped where none is available."""

import os
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from dwellwise_api.config import Settings
from dwellwise_api.main import create_app

pytestmark = pytest.mark.integration
psycopg = pytest.importorskip("psycopg")
URL = os.environ.get("DATABASE_URL")
SCHEMA = Path(__file__).resolve().parents[3] / "pipeline" / "sql" / "001_core.sql"

SQUARE = "ST_Multi(ST_Transform(ST_MakeEnvelope(%s, %s, %s, %s, 4326), 2157))"


@pytest.fixture
def client():
    if not URL:
        pytest.skip("DATABASE_URL not set")
    with psycopg.connect(URL, autocommit=True) as conn:
        conn.execute("drop schema if exists dw cascade")
        conn.execute(SCHEMA.read_text(encoding="utf-8"))
        snap = str(uuid.uuid4())
        conn.execute(
            "insert into dw.snapshot (id, source, fetched_at, raw_uri, sha256, rows_loaded, status) "
            "values (%s, 'settlements', now(), 'test://', 'x', 3, 'loaded')",
            (snap,),
        )
        for name, box in [
            ("KILDARE", (-7.2, 52.9, -6.5, 53.4)),
            ("MAYO", (-10.0, 53.5, -8.6, 54.3)),
            ("MEATH", (-7.2, 53.45, -6.2, 53.9)),
            ("LEITRIM", (-8.4, 53.8, -7.6, 54.4)),
        ]:
            conn.execute(f"insert into dw.county values (%s, {SQUARE}, %s)", (name, *box, snap))  # noqa: S608
        for code, name, key, county, box in [
            ("1", "Athy", "athy", "KILDARE", (-7.0, 53.0, -6.98, 53.01)),
            ("2", "Athboy", "athboy", "MEATH", (-6.93, 53.62, -6.91, 53.63)),
            ("3", "Castlebar", "castlebar", "MAYO", (-9.31, 53.85, -9.28, 53.87)),
            ("4", "Ballina", "ballina", "MAYO", (-9.17, 54.1, -9.14, 54.12)),
        ]:
            conn.execute(
                f"insert into dw.settlement values (%s, %s, %s, %s, {SQUARE}, %s)",  # noqa: S608 - constant SQL
                (code, name, key, county, *box, snap),
            )
    with TestClient(create_app(Settings(database_url=URL))) as c:
        yield c


def test_search_puts_the_exact_match_first(client):
    names = [s["name"] for s in client.get("/v1/settlements", params={"q": "ATHY"}).json()]
    assert names == ["Athy"]
    names = [s["name"] for s in client.get("/v1/settlements", params={"q": "ath"}).json()]
    assert names == ["Athy", "Athboy"]


def test_search_can_be_limited_to_a_county(client):
    found = client.get("/v1/settlements", params={"q": "ath", "county": "meath"}).json()
    assert [s["code"] for s in found] == ["2"]


def test_one_letter_matches_nothing_rather_than_everything(client):
    assert client.get("/v1/settlements", params={"q": "a"}).json() == []


def test_detail_has_location_area_and_sources(client):
    body = client.get("/v1/settlements/3").json()
    assert body["name"] == "Castlebar" and body["county"] == "MAYO"
    assert 53.85 < body["latitude"] < 53.87 and -9.31 < body["longitude"] < -9.28
    assert body["area_km2"] > 0
    assert [s["name"] for s in body["sources"]] == ["settlements"]


def test_unknown_code_is_a_404_in_the_error_shape(client):
    response = client.get("/v1/settlements/999")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_counties_list_every_county_with_its_settlement_count(client):
    assert client.get("/v1/counties").json() == [
        {"name": "KILDARE", "settlements": 1},
        {"name": "LEITRIM", "settlements": 0},
        {"name": "MAYO", "settlements": 2},
        {"name": "MEATH", "settlements": 1},
    ]


def test_a_countys_settlements_come_a_to_z_in_any_case(client):
    names = [s["name"] for s in client.get("/v1/counties/Mayo/settlements").json()]
    assert names == ["Ballina", "Castlebar"]
    assert client.get("/v1/counties/leitrim/settlements").json() == []


def test_an_unknown_county_is_a_404_not_an_empty_list(client):
    response = client.get("/v1/counties/Atlantis/settlements")
    assert response.status_code == 404
    assert response.json()["error"]["message"] == "No county is called Atlantis."


def test_ready_reports_the_missing_source(client):
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.json()["checks"]["data:counties"] == "never loaded"
    assert response.json()["checks"]["data:settlements"].endswith("h old")
