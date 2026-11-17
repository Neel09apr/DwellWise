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
