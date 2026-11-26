"""Runs against a real PostGIS in CI (DATABASE_URL); skipped where none is available."""

import os
from datetime import date, timedelta
from pathlib import Path

import pytest
from dwellwise_pipeline.run import register
from dwellwise_pipeline.sources import SOURCES
from fastapi.testclient import TestClient

from dwellwise_api.config import Settings
from dwellwise_api.main import create_app

from .seed import box, point, seed

pytestmark = pytest.mark.integration
psycopg = pytest.importorskip("psycopg")
URL = os.environ.get("DATABASE_URL")
SQL_DIR = Path(__file__).resolve().parents[3] / "pipeline" / "sql"

COUNTIES = [
    ("KILDARE", (-7.2, 52.9, -6.5, 53.4)),
    ("MAYO", (-10.0, 53.5, -8.6, 54.3)),
    ("MEATH", (-7.2, 53.45, -6.2, 53.9)),
    ("LEITRIM", (-8.4, 53.8, -7.6, 54.4)),
]
SETTLEMENTS = [  # code, name, box; the loader finds the county
    ("1", "Athy", (-7.0, 53.0, -6.98, 53.01)),
    ("2", "Athboy", (-6.93, 53.62, -6.91, 53.63)),
    ("3", "Castlebar", (-9.31, 53.85, -9.28, 53.87)),
    ("4", "Ballina", (-9.17, 54.1, -9.14, 54.12)),
]
ATHY = (-6.99, 53.005)
CASTLEBAR = (-9.295, 53.86)
OPEN_MAYO = (-9.0, 53.9)  # in Mayo, in no town
OPEN_KILDARE = (-6.8, 53.2)  # in Kildare, in no town

APPLICATIONS = [  # number, county, received, class, residential, where; the loader finds the town
    ("K1", "KILDARE", "2026-10-05", "granted", True, ATHY),
    ("K2", "KILDARE", "2026-10-20", "refused", False, ATHY),
    ("K3", "KILDARE", "2026-09-01", "pending", True, ATHY),
    ("K4", "KILDARE", "2019-06-01", "granted", True, ATHY),  # older than the brief's five years
    ("M1", "MAYO", "2026-10-10", "granted", False, OPEN_MAYO),
    ("M2", "MAYO", "2025-01-15", "granted", True, CASTLEBAR),  # outside the stats ranges asked for below
]


# Around Athy (-7.0, 53.0, -6.98, 53.01); at this latitude 0.01 degrees of longitude is about 670 m.
PROTECTED = [  # designation, code, box
    ("SAC", "000001", (-6.99, 53.0, -6.97, 53.01)),  # overlaps the town
    ("SPA", "004001", (-6.9725, 53.0, -6.96, 53.01)),  # about 500 m east
    ("NHA", "000001", (-6.935, 53.0, -6.92, 53.01)),  # about 3 km east; same code as the SAC
    ("SAC", "000002", (-6.86, 53.0, -6.85, 53.01)),  # about 8 km east: outside 5 km
]


def application(number, county, received, cls, residential, where) -> dict:
    return {
        "authority": "Test Council", "application_number": number, "received": received, "decided": None,
        "decision": None, "decision_class": cls, "recognised": True, "county": county, "units_stated": None,
        "residential": residential, "geometry": point(*where),
    }  # fmt: skip


def site(designation: str, code: str, where: tuple) -> dict:
    return {
        "designation": designation,
        "site_code": code,
        "name": f"Site {code}",
        "url": None,
        "geometry": box(*where),
    }


@pytest.fixture
def client():
    if not URL:
        pytest.skip("DATABASE_URL not set")
    with psycopg.connect(URL, autocommit=True) as conn:
        conn.execute("drop schema if exists dw cascade")
        for sql in sorted(SQL_DIR.glob("*.sql")):
            conn.execute(sql.read_text(encoding="utf-8"))
        seed(conn, "counties", [{"name": n, "geometry": box(*b)} for n, b in COUNTIES])
        towns = [
            {"code": c, "name": n, "name_key": n.lower(), "geometry": box(*b)} for c, n, b in SETTLEMENTS
        ]
        seed(conn, "settlements", towns)
        seed(conn, "planning", [application(*a) for a in APPLICATIONS])
        for name in ("sac", "spa", "nha"):  # one designation per run, as the pipeline loads them
            seed(conn, name, [site(*p) for p in PROTECTED if p[0] == name.upper()])
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
    loaded = ["counties", "settlements", "planning", "sac", "spa", "nha"]  # in the pipeline's order
    assert [s["name"] for s in body["sources"]] == loaded
    assert body["sources"][0]["attribution"] == SOURCES["counties"].attribution


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
    assert client.get("/ready").status_code == 200  # every seeded source has just loaded
    with psycopg.connect(URL, autocommit=True) as conn:
        register(conn, SOURCES["commencements"])  # a first run that failed before loading
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.json()["checks"]["data:commencements"] == "never loaded"
    assert response.json()["checks"]["data:settlements"].endswith("h old")


def test_stats_count_applications_by_month_and_class_across_ireland(client):
    body = client.get("/v1/stats/applications", params={"from": "2026-08", "to": "2026-10"}).json()
    assert body["county"] is None and body["captured_at"]
    assert body["totals"] == {
        "granted": 2,
        "refused": 1,
        "pending": 1,
        "withdrawn": 0,
        "other": 0,
        "total": 4,
    }
    assert [(m["month"], m["total"]) for m in body["months"]] == [
        ("2026-08", 0),
        ("2026-09", 1),
        ("2026-10", 3),
    ]
    by_county = {c["county"]: c["total"] for c in body["counties"]}
    assert by_county == {"KILDARE": 3, "LEITRIM": 0, "MAYO": 1, "MEATH": 0}


def test_stats_for_one_county_can_keep_only_residential(client):
    params = {"county": "kildare", "residential": "true", "from": "2026-09", "to": "2026-10"}
    body = client.get("/v1/stats/applications", params=params).json()
    assert body["county"] == "KILDARE" and body["residential"] is True
    assert (body["totals"]["granted"], body["totals"]["pending"], body["totals"]["total"]) == (1, 1, 2)
    assert [c["county"] for c in body["counties"]] == ["KILDARE"]


def test_stats_for_an_unknown_county_is_a_404(client):
    response = client.get("/v1/stats/applications", params={"county": "Atlantis"})
    assert response.status_code == 404
    assert response.json()["error"]["message"] == "No county is called Atlantis."


def test_metrics_report_data_age_without_anyone_calling_ready(client):
    from dwellwise_api.metrics import DATA_AGE

    DATA_AGE.clear()  # nothing set by earlier /ready calls
    body = client.get("/metrics").text
    assert 'dwellwise_data_age_hours{source="planning"}' in body
    assert 'dwellwise_data_age_hours{source="settlements"}' in body


def test_the_brief_counts_recent_residential_applications_in_the_town(client):
    body = client.get("/v1/settlements/1/brief").json()
    p = body["precedents"]
    assert p["years"] == 5
    assert (p["residential"]["granted"], p["residential"]["pending"], p["residential"]["total"]) == (1, 1, 2)
    assert p["all_applications"] == 3  # K4 is older than five years
    assert [a["application_number"] for a in p["recent"]] == ["K1", "K3"]  # newest first, residential only
    assert body["pending"] == ["wastewater", "alternatives"]


def test_a_town_without_applications_has_an_empty_section_not_an_error(client):
    p = client.get("/v1/settlements/4/brief").json()["precedents"]
    assert (p["residential"]["total"], p["all_applications"], p["recent"]) == (0, 0, [])


def test_the_brief_for_an_unknown_settlement_is_a_404(client):
    assert client.get("/v1/settlements/999/brief").status_code == 404


def test_the_brief_lists_protected_sites_within_5_km_nearest_first(client):
    sites = client.get("/v1/settlements/1/brief").json()["protected"]["sites"]
    assert [(x["designation"], x["site_code"], x["band"]) for x in sites] == [
        ("SAC", "000001", "touches"),
        ("SPA", "004001", "1km"),
        ("NHA", "000001", "5km"),
    ]
    assert sites[0]["distance_m"] == 0 and 400 < sites[1]["distance_m"] < 600


def test_a_town_far_from_protected_sites_has_an_empty_list(client):
    assert client.get("/v1/settlements/3/brief").json()["protected"]["sites"] == []


def seed_commencements(conn) -> None:
    submitted = (date.today() - timedelta(days=2)).isoformat()
    notices = [  # all in Kildare; the loader finds the town
        ("CN1", "Athy Meadows", 9, "2026-10-12", ATHY),
        ("CN2", None, 1, "2026-10-20", ATHY),  # a one-off house: counted, never listed
        ("CN3", "Old Scheme", 20, "2025-02-01", OPEN_KILDARE),  # outside the months asked for, still listed
    ]
    seed(conn, "commencements", [
        {
            "notice_number": number, "local_authority": "Kildare County Council", "county": "KILDARE",
            "submitted": submitted, "commenced": commenced, "expected_end": None, "homes": homes,
            "scheme_homes": None, "homes_completed": 0, "planning_ref": None, "project_name": name,
            "routing_key": None, "geometry": point(*where),
        }
        for number, name, homes, commenced, where in notices
    ])  # fmt: skip


def test_commencements_count_homes_and_list_only_schemes_of_five_or_more(client):
    with psycopg.connect(URL, autocommit=True) as conn:
        seed_commencements(conn)
    body = client.get(
        "/v1/stats/commencements", params={"county": "kildare", "from": "2026-09", "to": "2026-10"}
    ).json()
    assert body["totals"] == {"notices": 2, "homes": 10}
    assert [(m["month"], m["homes"]) for m in body["months"]] == [("2026-09", 0), ("2026-10", 10)]
    assert body["last_7_days"] == {"notices": 3, "homes": 30}
    assert [s["notice_number"] for s in body["recent_schemes"]] == ["CN1", "CN3"]
    assert body["recent_schemes"][0]["settlement"] == "Athy"
    assert body["captured_at"] and body["newest_submitted"]

    town = client.get(
        "/v1/stats/commencements", params={"settlement": "1", "from": "2026-10", "to": "2026-10"}
    )
    assert town.json()["totals"] == {"notices": 2, "homes": 10}
    assert client.get("/v1/stats/commencements", params={"settlement": "9999"}).status_code == 404


def test_planning_stats_say_how_recent_the_source_is(client):
    body = client.get("/v1/stats/applications", params={"county": "mayo"}).json()
    assert body["newest_received"] == "2026-10-10"


def test_the_map_shows_schemes_of_five_homes_or_more_from_the_last_year(client):
    with psycopg.connect(URL, autocommit=True) as conn:
        seed_commencements(conn)  # CN1 (9 homes) is recent; CN2 is one house; CN3 started in 2025-02
        conn.execute(
            "update dw.planning_application set units_stated = 12, received = current_date - 10 "
            "where application_number = 'K1'"
        )
        conn.execute("update dw.commencement set commenced = current_date - 30 where notice_number = 'CN1'")
    body = client.get("/v1/map/developments", params={"county": "kildare"}).json()
    kinds = sorted((f["properties"]["kind"], f["properties"]["homes"]) for f in body["features"])
    assert kinds == [("applied", 12), ("started", 9)]
    lng, lat = body["features"][0]["geometry"]["coordinates"]
    assert round(lng, 4) == lng and 52 < lat < 54
    # Seeded applications state no units, except K1: Test Council states them on 1 in 3 recent ones.
    assert body["sparse_units"] == []
    with psycopg.connect(URL, autocommit=True) as conn:
        conn.execute("update dw.planning_application set units_stated = null")
    body = client.get("/v1/map/developments", params={"county": "kildare"}).json()
    assert body["sparse_units"] == [{"authority": "Test Council", "share": 0}]
    assert client.get("/v1/map/developments", params={"county": "Atlantis"}).status_code == 404


def test_prices_follow_the_towns_routing_key_or_fall_back_to_the_county(client):
    with psycopg.connect(URL, autocommit=True) as conn:
        seed_commencements(conn)  # CN1 and CN2 are in Athy (settlement 1)
        conn.execute("update dw.commencement set routing_key = 'R14' where notice_number in ('CN1', 'CN2')")
        month = (date.today().replace(day=1) - timedelta(days=32)).replace(day=1).isoformat()  # 2 months ago
        areas = [("eircode", "R14", "Athy"), ("region", "-", "All"), ("region", "22", "Kildare")]
        seed(conn, "prices", [
            {"kind": kind, "code": code, "name": name, "month": month, "status": "all",
             "sales": 30, "median": 350000, "mean": 360000}
            for kind, code, name in areas
        ])  # fmt: skip
    town = client.get("/v1/prices", params={"settlement": "1"}).json()
    assert [(a["kind"], a["code"], a["latest"]["median"]) for a in town["areas"]] == [
        ("eircode", "R14", 350000)
    ]
    assert town["basis"].startswith("Eircode area R14: 2 of the 2 construction notices")

    # Athboy (Meath) has no notices and Meath has no price rows here: the national figures, said as such.
    other = client.get("/v1/prices", params={"settlement": "2"}).json()
    assert [a["name"] for a in other["areas"]] == ["All"] and other["basis"] == "Figures for all of Ireland."

    county = client.get("/v1/prices", params={"county": "kildare"}).json()
    assert [a["name"] for a in county["areas"]] == ["Kildare"]
    assert client.get("/v1/prices").json()["areas"][0]["name"] == "All"
    assert client.get("/v1/prices", params={"settlement": "9999"}).status_code == 404


def test_a_county_and_a_town_together_are_refused_not_answered_wrongly(client):
    # Castlebar (3) is in Mayo: commencements used to return 0 homes here, and prices ignored the county.
    for path in ("/v1/stats/commencements", "/v1/prices"):
        response = client.get(path, params={"county": "kildare", "settlement": "3"})
        assert response.status_code == 422
        assert response.json()["error"]["message"] == "Give a county or a settlement, not both."


def test_search_with_an_unknown_county_is_a_404(client):
    response = client.get("/v1/settlements", params={"q": "ath", "county": "Atlantis"})
    assert response.status_code == 404


def test_ready_follows_the_registry_and_an_empty_one_is_not_ready(client):
    with psycopg.connect(URL, autocommit=True) as conn:
        conn.execute(
            "insert into dw.source (name, attribution, position) values ('newsource', 'New. CC BY 4.0.', 9)"
        )
    checks = client.get("/ready").json()["checks"]
    assert checks["data:newsource"] == "never loaded"  # registered by a first run that has not loaded yet
    with psycopg.connect(URL, autocommit=True) as conn:
        conn.execute("delete from dw.source")
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.json()["checks"]["sources"] == "none registered"


def test_the_shortlist_puts_a_countys_towns_side_by_side(client):
    with psycopg.connect(URL, autocommit=True) as conn:
        seed_commencements(conn)  # CN1 (9 homes) and CN2 (1 home) are in Athy
        conn.execute("update dw.commencement set commenced = current_date - 30, routing_key = 'R14' "
                     "where notice_number in ('CN1', 'CN2')")  # fmt: skip
        month = (date.today().replace(day=1) - timedelta(days=32)).replace(day=1).isoformat()
        seed(conn, "prices", [{"kind": "eircode", "code": "R14", "name": "Athy", "month": month,
                               "status": "all", "sales": 30, "median": 350000, "mean": 360000}])  # fmt: skip
    body = client.get("/v1/shortlist", params={"county": "kildare"}).json()
    assert (body["county"], body["sort"], body["towns_in_county"]) == ("KILDARE", "started", 1)
    (athy,) = body["towns"]
    # K1 granted and K3 pending are residential; K2 is not; K4 is older than five years.
    assert (athy["granted"], athy["refused"], athy["pending"]) == (1, 0, 1)
    assert athy["homes_started"] == 10
    assert athy["protected_within_1km"] == 2  # the SAC that overlaps and the SPA 500 m away, not the NHA
    assert (athy["price_area"], athy["median_price"], athy["price_month"]) == ("R14", 350000, month[:7])

    # Mayo: neither town started homes; Castlebar has a residential grant (M2), so it comes first.
    mayo = client.get("/v1/shortlist", params={"county": "Mayo"}).json()
    assert [t["name"] for t in mayo["towns"]] == ["Castlebar", "Ballina"]
    assert mayo["towns"][1]["median_price"] is None
    assert client.get("/v1/shortlist", params={"county": "Atlantis"}).status_code == 404
    assert client.get("/v1/shortlist").status_code == 422
    assert client.get("/v1/shortlist", params={"county": "mayo", "sort": "score"}).status_code == 422
