"""Commencement stats without a database: one round trip, months filled, unknown places refused."""

from datetime import date

from dwellwise_api.building import commencement_stats

from .test_stats import TODAY, CountingConn

ROW = {
    "county_known": True,
    "settlement_known": True,
    "captured_at": None,
    "newest_submitted": date(2026, 11, 16),
    "months": [{"month": "2026-10", "notices": 4, "homes": 30}],
    "last_7_days": {"notices": 2, "homes": 11},
    "recent_schemes": [
        {
            "notice_number": "CN1", "project_name": "Bunclody Woods", "settlement": "Bunclody",
            "county": "CARLOW", "local_authority": "Carlow County Council", "homes": 9, "scheme_homes": 27,
            "commenced": "2026-12-01", "expected_end": "2027-10-01", "planning_ref": "23/68",
        }
    ],
}  # fmt: skip


def test_commencements_need_one_round_trip_and_fill_empty_months():
    conn = CountingConn(ROW)
    found = commencement_stats(conn, None, None, "2026-09", "2026-11", TODAY)
    assert conn.queries == 1
    assert [(m.month, m.homes) for m in found.months] == [("2026-09", 0), ("2026-10", 30), ("2026-11", 0)]
    assert (found.totals.notices, found.totals.homes) == (4, 30)
    assert (found.last_7_days.homes, found.newest_submitted) == (11, date(2026, 11, 16))
    assert found.recent_schemes[0].project_name == "Bunclody Woods"


def test_an_unknown_county_or_settlement_is_none():
    assert (
        commencement_stats(CountingConn({**ROW, "county_known": False}), "atlantis", None, None, None, TODAY)
        is None
    )
    assert (
        commencement_stats(CountingConn({**ROW, "settlement_known": False}), None, "99999", None, None, TODAY)
        is None
    )
