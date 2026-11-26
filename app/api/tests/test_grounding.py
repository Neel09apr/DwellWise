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


def test_narrow_and_no_break_spaces_group_thousands_but_ordinary_spaces_do_not():
    for space in (" ", " ", " "):
        assert numbers(f"€420{space}000 and 1{space}234{space}567") == {Decimal("420000"), Decimal("1234567")}
    assert numbers("8 110") == {Decimal("8"), Decimal("110")}
    assert numbers("code 1") == {Decimal("1")}  # not a group of three
    assert numbers("1 23") == {Decimal("1"), Decimal("23")}  # two digits after the space: not a group
