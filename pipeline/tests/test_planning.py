"""The planning source: decision classes, counties, residential flag, and its run checks."""

import pytest

from dwellwise_pipeline.sources import SOURCES
from dwellwise_pipeline.sources.planning import AUTHORITY_COUNTY, CLASSES, check, classify, is_residential

from .conftest import collection

COUNTIES_26 = {
    "CARLOW", "CAVAN", "CLARE", "CORK", "DONEGAL", "DUBLIN", "GALWAY", "KERRY", "KILDARE",
    "KILKENNY", "LAOIS", "LEITRIM", "LIMERICK", "LONGFORD", "LOUTH", "MAYO", "MEATH", "MONAGHAN",
    "OFFALY", "ROSCOMMON", "SLIGO", "TIPPERARY", "WATERFORD", "WESTMEATH", "WEXFORD", "WICKLOW",
}  # fmt: skip


# Real wordings seen in the national dataset (trailing spaces included).
@pytest.mark.parametrize(
    ("decision", "expected"),
    [
        ("CONDITIONAL", "granted"),
        ("Grant Permission              ", "granted"),
        ("Granted (Conditional)", "granted"),
        ("UNCONDITIONAL", "granted"),
        ("GRANT PERMISSION FOR RETENTION", "granted"),
        ("GRANT PERMISSION & GRANT RETENTION", "granted"),
        ("REFUSED", "refused"),
        ("REFUSE PERMISSION", "refused"),
        ("REFUSE PERMISSION & REFUSE RETENTION              ", "refused"),
        ("REFUSE EXT. OF DURATION OF PERMISSION", "refused"),
        ("GRANT PERMISSION & REFUSE PERMISSION", "other"),
        ("SPLIT DECISION(PERMISSION", "other"),
        ("APPLICATION DECLARED INVALID", "other"),
        ("Invalid - Site Notice", "other"),
        ("Declared Not Exempt", "other"),
        ("S5 DEC EXEMPT", "other"),
        ("GRANT CERTIFICATE OF EXEMPTION", "other"),
        ("WITHDRAW THE APPLICATION", "withdrawn"),
        ("App withdrawn as no AI recd in 6 months           ", "withdrawn"),
        ("REQUEST ADDITIONAL INFORMATION", "pending"),
        ("APPLICATION DECLARED INVA", "other"),  # cut short in the source data
        ("REQUEST AI EXT OF TIME", "pending"),
        ("S5 REQ AI", "pending"),
    ],
)
def test_council_wordings_map_to_their_class(decision, expected):
    assert classify(decision, None, 1, None) == (expected, True)


def test_unknown_wording_is_other_and_flagged_not_guessed():
    assert classify("PERMISSION FOR SOMETHING NEW", None, 1, None) == ("other", False)


def test_a_withdrawn_date_wins_over_the_decision_text():
    assert classify("CONDITIONAL", None, 1, 1700000000000) == ("withdrawn", True)


@pytest.mark.parametrize(
    ("decision", "status", "decided", "expected"),
    [
        ("N/A", "INCOMPLETED APPLICATION", None, ("other", True)),
        ("", "DEEMED WITHDRAWN", None, ("withdrawn", True)),
        (None, "Invalid - Case Closed", None, ("other", True)),
        ("N/A", "New Application", None, ("pending", True)),
        ("", "FURTHER INFORMATION", None, ("pending", True)),
        ("", "Decision", 1700000000000, ("other", False)),  # decided, but no wording to read
    ],
)
def test_blank_decisions_fall_back_to_the_status(decision, status, decided, expected):
    assert classify(decision, status, decided, None) == expected


def test_every_class_is_allowed_by_the_table():
    assert set(CLASSES) == {"granted", "refused", "pending", "withdrawn", "other"}


def test_every_authority_maps_to_one_of_the_26_counties():
    assert len(AUTHORITY_COUNTY) == 31
    assert set(AUTHORITY_COUNTY.values()) == COUNTIES_26


@pytest.mark.parametrize(
    ("units", "one_off", "expected"),
    [
        (4, None, True),
        (0, " ", False),
        (None, "Y", True),
        (None, "Single House    ", True),
        (None, "No", False),
    ],
)
def test_residential_means_dwellings_are_stated(units, one_off, expected):
    assert is_residential(units, one_off) is expected


def feature(**props) -> dict:
    base = {
        "PlanningAuthority": "Cork County Council ",
        "ApplicationNumber": " 25/392",
        "ReceivedDate": 1752451200000,  # 2025-07-14
        "DecisionDate": 1774310400000,  # 2026-03-24
        "WithdrawnDate": None,
        "Decision": "Grant with Conditions         ",
        "ApplicationStatus": "APPLICATION FINALISED",
        "NumResidentialUnits": None,
        "OneOffHouse": "Y",
    }
    return {
        "type": "Feature",
        "properties": {**base, **props},
        "geometry": {"type": "Point", "coordinates": [-8.5, 51.95]},
    }


def test_transform_trims_maps_and_converts_dates():
    (row,) = SOURCES["planning"].transform(collection([feature()]))
    assert row["authority"] == "Cork County Council"
    assert row["application_number"] == "25/392"
    assert row["county"] == "CORK"
    assert (row["received"], row["decided"]) == ("2025-07-14", "2026-03-24")
    assert row["decision"] == "Grant with Conditions"
    assert (row["decision_class"], row["recognised"], row["residential"]) == ("granted", True, True)


def test_an_unknown_authority_is_reported_before_load():
    problems = check(collection([feature(), feature(PlanningAuthority="Narnia County Council")]))
    assert problems == ["unknown planning authorities: Narnia County Council"]


def test_the_query_is_limited_and_never_asks_for_applicants():
    source = SOURCES["planning"]
    assert source.where == "ReceivedDate >= DATE '2020-01-01'"
    assert not [f for f in source.out_fields if f.lower().startswith(("applicant", "agent"))]
