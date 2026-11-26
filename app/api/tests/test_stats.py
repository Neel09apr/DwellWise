"""Planning stats without a database: the error shape, and one round trip."""

from datetime import date

import pytest
from fastapi.testclient import TestClient

from dwellwise_api.config import Settings
from dwellwise_api.db import get_conn
from dwellwise_api.main import create_app
from dwellwise_api.months import Months
from dwellwise_api.place import Place

from .fakes import memory_places

TODAY = date(2026, 11, 17)


@pytest.fixture
def offline():
    app = create_app(Settings())
    app.dependency_overrides[get_conn] = lambda: None  # these requests fail before any SQL
    app.state.places = memory_places()
    with TestClient(app) as c:
        yield c


def test_a_bad_month_is_a_422_in_the_error_shape(offline):
    response = offline.get("/v1/stats/applications", params={"from": "2025-13"})
    assert response.status_code == 422
    assert response.json()["error"]["message"].startswith("from:")


@pytest.mark.parametrize("path", ["/v1/stats/applications", "/v1/stats/commencements"])
@pytest.mark.parametrize(
    ("params", "message"),
    [
        ({"from": "2025-03", "to": "2025-01"}, "from must not be after to."),
        ({"from": "2016-01", "to": "2026-11"}, "The range may span at most 120 months."),
    ],
)
def test_a_bad_range_is_a_422_with_a_plain_message_on_every_endpoint(offline, path, params, message):
    response = offline.get(path, params=params)
    assert response.status_code == 422
    assert response.json() == {"error": {"code": "unprocessable_content", "message": message}}


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
    stats = application_stats(
        conn, Place(counties=("CORK", "MAYO")), None, Months.between("2026-09", "2026-10", TODAY)
    )
    assert conn.queries == 1
    assert (stats.totals.granted, stats.totals.refused, stats.totals.total) == (3, 1, 4)
    assert [(m.month, m.total) for m in stats.months] == [("2026-09", 0), ("2026-10", 4)]
    assert [(c.county, c.total) for c in stats.counties] == [("CORK", 3), ("MAYO", 1)]
