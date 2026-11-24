"""Month arithmetic and range rules: no database needed."""

from datetime import date

import pytest
from fastapi.testclient import TestClient

from dwellwise_api.config import Settings
from dwellwise_api.db import get_conn
from dwellwise_api.main import create_app
from dwellwise_api.stats import RangeError, add_months, month_range

TODAY = date(2026, 11, 17)


def test_the_default_is_the_last_twelve_months_including_this_one():
    assert month_range(None, None, TODAY) == (date(2025, 12, 1), date(2026, 11, 1))


def test_a_given_range_is_kept_and_crosses_years():
    assert month_range("2024-11", "2025-02", TODAY) == (date(2024, 11, 1), date(2025, 2, 1))


def test_from_after_to_is_refused():
    with pytest.raises(RangeError, match="from must not be after to"):
        month_range("2025-03", "2025-02", TODAY)


def test_more_than_ten_years_is_refused_but_exactly_ten_is_allowed():
    assert month_range("2016-12", "2026-11", TODAY)[0] == date(2016, 12, 1)
    with pytest.raises(RangeError, match="at most 120 months"):
        month_range("2016-11", "2026-11", TODAY)


@pytest.mark.parametrize(
    ("day", "n", "expected"),
    [
        (date(2025, 12, 1), 1, date(2026, 1, 1)),
        (date(2026, 1, 1), -1, date(2025, 12, 1)),
        (date(2026, 3, 1), -14, date(2025, 1, 1)),
    ],
)
def test_months_add_across_year_ends(day, n, expected):
    assert add_months(day, n) == expected


@pytest.fixture
def offline():
    app = create_app(Settings())
    app.dependency_overrides[get_conn] = lambda: None  # these requests fail before any SQL
    with TestClient(app) as c:
        yield c


def test_a_bad_month_is_a_422_in_the_error_shape(offline):
    response = offline.get("/v1/stats/applications", params={"from": "2025-13"})
    assert response.status_code == 422
    assert response.json()["error"]["message"].startswith("from:")


def test_a_reversed_range_is_a_422_with_a_plain_message(offline):
    response = offline.get("/v1/stats/applications", params={"from": "2025-03", "to": "2025-01"})
    assert response.status_code == 422
    assert response.json() == {
        "error": {"code": "unprocessable_content", "message": "from must not be after to."}
    }


class CountingConn:
    """Stands in for a psycopg connection: answers every query with one row and counts them."""

    def __init__(self, row):
        self.row = row
        self.queries = 0

    def cursor(self, row_factory=None):
        conn = self

        class Cursor:
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def execute(self, _sql, _params=None):
                conn.queries += 1

            def fetchone(self):
                return conn.row

        return Cursor()


ROW = {
    "counties": ["CORK", "MAYO"],
    "rows": [
        {"county": "CORK", "month": "2026-10-01", "decision_class": "granted", "n": 3},
        {"county": "MAYO", "month": "2026-10-01", "decision_class": "refused", "n": 1},
    ],
    "captured_at": None,
    "newest_received": None,
}


def test_the_stats_need_exactly_one_database_round_trip():
    from dwellwise_api.stats import application_stats

    conn = CountingConn(ROW)
    stats = application_stats(conn, None, None, "2026-09", "2026-10", TODAY)
    assert conn.queries == 1
    assert (stats.totals.granted, stats.totals.refused, stats.totals.total) == (3, 1, 4)
    assert [(m.month, m.total) for m in stats.months] == [("2026-09", 0), ("2026-10", 4)]
    assert [(c.county, c.total) for c in stats.counties] == [("CORK", 3), ("MAYO", 1)]


def test_an_unknown_county_is_none_after_the_same_single_query():
    from dwellwise_api.stats import application_stats

    conn = CountingConn(ROW)
    assert application_stats(conn, "atlantis", None, None, None, TODAY) is None
    assert conn.queries == 1
