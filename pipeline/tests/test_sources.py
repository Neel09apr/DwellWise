import json

from dwellwise_pipeline.sources import SOURCES


def test_counties_are_upper_cased_and_trimmed(counties):
    rows = SOURCES["counties"].transform(counties)
    assert [r["name"] for r in rows] == ["CORK", "KERRY"]
    assert json.loads(rows[0]["geometry"])["type"] == "Polygon"


def test_settlements_keep_their_code_as_text_and_get_a_name_key(settlements):
    rows = SOURCES["settlements"].transform(settlements)
    assert rows[0]["code"] == "1001"
    assert rows[0]["name"] == "Baile Átha Fhirdhia"
    assert rows[0]["name_key"] == "baileathafhirdhia"
    assert rows[1]["name_key"] == "carrickonshannon"


def test_counties_load_before_settlements():
    assert list(SOURCES) == ["counties", "settlements"]
