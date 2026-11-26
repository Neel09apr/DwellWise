"""The grounding check on its own: numbers compared by value, nothing derived."""

from decimal import Decimal

from dwellwise_api.grounding import numbers, ungrounded


def test_separators_and_trailing_zeros_do_not_matter():
    found = numbers("€420,000 and 12.50% in 2026-09")
    assert found == {Decimal("420000"), Decimal("12.5"), Decimal("2026"), Decimal("9")}


def test_only_numbers_found_in_a_source_pass():
    sources = ['{"median":420000,"month":"2026-09","sales":61}']
    assert ungrounded("The median was €420,000 in 2026-09 from 61 sales.", sources) == set()
    assert ungrounded("About €420k.", sources) == {Decimal("420")}
    assert ungrounded("Up 5% on last year.", sources) == {Decimal("5")}


def test_an_answer_without_numbers_needs_no_source():
    assert ungrounded("There is no county called Atlantis.", []) == set()
