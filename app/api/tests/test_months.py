"""Month arithmetic and range rules: no database needed."""

from datetime import date

import pytest

from dwellwise_api.months import Months, RangeError, add_months

TODAY = date(2026, 11, 17)


def test_the_default_is_the_last_twelve_months_including_this_one():
    months = Months.between(None, None, TODAY)
    assert (months.first, months.last) == (date(2025, 12, 1), date(2026, 11, 1))
    assert len(list(months.each())) == 12


def test_a_given_range_is_kept_and_crosses_years():
    months = Months.between("2024-11", "2025-02", TODAY)
    assert list(months.each()) == ["2024-11", "2024-12", "2025-01", "2025-02"]
    assert (months.from_label, months.to_label) == ("2024-11", "2025-02")
    assert months.end == date(2025, 3, 1)  # queries read [first, end)


def test_one_month_is_a_range_of_one():
    assert list(Months.between("2025-02", "2025-02", TODAY).each()) == ["2025-02"]


def test_from_after_to_is_refused():
    with pytest.raises(RangeError, match="from must not be after to"):
        Months.between("2025-03", "2025-02", TODAY)


def test_more_than_ten_years_is_refused_but_exactly_ten_is_allowed():
    assert Months.between("2016-12", "2026-11", TODAY).first == date(2016, 12, 1)
    with pytest.raises(RangeError, match="at most 120 months"):
        Months.between("2016-11", "2026-11", TODAY)


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
