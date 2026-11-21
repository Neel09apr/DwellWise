"""The brief's rules without a database: the window and the single round trip."""

from datetime import date

from dwellwise_api.brief import PRECEDENT_YEARS, brief, years_before

from .test_stats import CountingConn

TODAY = date(2026, 11, 21)


def test_the_window_is_five_years_to_the_day():
    assert PRECEDENT_YEARS == 5
    assert years_before(TODAY, 5) == date(2021, 11, 21)


def test_a_leap_day_falls_back_to_the_28th():
    assert years_before(date(2028, 2, 29), 5) == date(2023, 2, 28)


ROW = {
    "found": True,
    "residential": {"granted": 3, "refused": 1},
    "all_total": 9,
    "recent": [
        {
            "authority": "Mayo County Council",
            "application_number": "25/101",
            "received": "2026-10-02",
            "decided": None,
            "decision": None,
            "decision_class": "pending",
            "units_stated": 1,
        }
    ],
    "captured_at": None,
}


def test_the_brief_needs_one_round_trip_and_fills_missing_classes_with_zero():
    conn = CountingConn(ROW)
    b = brief(conn, "3", TODAY)
    assert conn.queries == 1
    r = b.precedents.residential
    assert (r.granted, r.refused, r.pending, r.withdrawn, r.other, r.total) == (3, 1, 0, 0, 0, 4)
    assert b.precedents.all_applications == 9
    assert b.precedents.since == date(2021, 11, 21)
    assert b.precedents.recent[0].received == date(2026, 10, 2)
    assert b.pending == ["wastewater", "protected", "alternatives"]


def test_an_unknown_settlement_is_none():
    assert brief(CountingConn({**ROW, "found": False}), "999", TODAY) is None
