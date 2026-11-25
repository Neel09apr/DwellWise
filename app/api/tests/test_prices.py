"""Price areas without a database: which area a place gets, and how months are folded."""

from datetime import date

from dwellwise_api.place import Place
from dwellwise_api.prices import choose, prices

from .test_stats import CountingConn


def row(kind, code, name, month, status="all", sales=10, median=400_000):
    return {
        "kind": kind, "code": code, "name": name, "month": month, "status": status,
        "sales": sales, "median": median,
    }  # fmt: skip


REGIONS = [
    row("region", "-", "All", "2026-09-01"),
    row("region", "39", "Cork City", "2026-09-01"),
    row("region", "40", "Cork County", "2026-09-01"),
    row("region", "25", "Meath", "2026-09-01"),
]


def test_a_town_gets_the_routing_key_most_of_its_notices_carry():
    key = {"routing_key": "C15", "notices": 40, "with_eircode": 52}
    picks, basis = choose({"rows": REGIONS, "county": "MEATH", "key": key, "settlement": "11016"})
    assert picks == [("eircode", "C15")]
    assert basis.startswith("Eircode area C15: 40 of the 52 construction notices")


def test_a_town_without_an_eircode_falls_back_to_its_county_and_says_so():
    picks, basis = choose({"rows": REGIONS, "county": "MEATH", "key": None, "settlement": "1"})
    assert picks == [("region", "25")]
    assert "no construction notice in this town gives an Eircode" in basis


def test_a_split_county_shows_each_part_and_ireland_shows_the_national_row():
    picks, _ = choose({"rows": REGIONS, "county": "CORK", "key": None})
    assert picks == [("region", "39"), ("region", "40")]
    assert choose({"rows": REGIONS, "county": None, "key": None})[0] == [("region", "-")]


def test_months_fold_all_and_new_homes_and_the_latest_needs_a_median():
    data = {
        "key": None, "captured_at": None,
        "rows": [
            row("region", "-", "All", "2026-08-01"),
            row("region", "-", "All", "2026-08-01", status="new", sales=3, median=460_000),
            row("region", "-", "All", "2026-09-01", sales=None, median=None),
        ],
    }  # fmt: skip
    conn = CountingConn(data)
    found = prices(conn, Place(), date(2026, 11, 25))
    assert conn.queries == 1
    (area,) = found.areas
    assert [(m.month, m.median, m.new_median) for m in area.months] == [
        ("2026-08", 400_000, 460_000),
        ("2026-09", None, None),
    ]
    assert area.latest.month == "2026-08"  # September is suppressed
    assert area.sales_12_months == 10
