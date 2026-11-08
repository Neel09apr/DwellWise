import pytest

from dwellwise_pipeline.sources import SOURCES
from dwellwise_pipeline.validate import ValidationError, validate

from .conftest import collection, square

SETTLEMENTS = SOURCES["settlements"]


def rows(n: int, **extra) -> dict:
    return collection(
        [
            {
                "type": "Feature",
                "properties": {"SETTLEMENT": str(i), "SETTL_NAME": f"Town {i}", **extra},
                "geometry": square(0, 0, 1, 1),
            }
            for i in range(n)
        ]
    )


def test_a_clean_collection_passes():
    validate(SETTLEMENTS, rows(850), previous_rows=873)


def test_too_few_rows_are_rejected():
    with pytest.raises(ValidationError, match="expected at least 800"):
        validate(SETTLEMENTS, rows(10), previous_rows=None)


def test_a_large_swing_from_the_last_run_is_rejected():
    with pytest.raises(ValidationError, match="more than 20% change"):
        validate(SETTLEMENTS, rows(1100), previous_rows=873)


def test_personal_data_fields_are_rejected_whatever_their_spelling():
    with pytest.raises(ValidationError, match="personal-data fields present: Applicant_Name"):
        validate(SETTLEMENTS, rows(850, Applicant_Name="someone"), previous_rows=None)


def test_missing_required_values_and_geometry_are_rejected():
    data = rows(850)
    data["features"][0]["properties"]["SETTL_NAME"] = ""
    data["features"][1]["geometry"] = None
    with pytest.raises(ValidationError) as err:
        validate(SETTLEMENTS, data, previous_rows=None)
    assert "1 rows missing SETTL_NAME" in str(err.value)
    assert "1 rows without geometry" in str(err.value)
