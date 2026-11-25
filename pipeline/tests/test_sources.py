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


def test_every_source_comes_after_the_sources_it_needs():
    order = list(SOURCES)
    for name, source in SOURCES.items():
        for needed in source.after:
            assert needed in SOURCES, f"{name} needs {needed}, which is not a source"
            assert order.index(needed) < order.index(name), f"{name} must come after {needed}"
    assert SOURCES["settlements"].after == ("counties",)
    assert SOURCES["planning"].after == SOURCES["commencements"].after == ("settlements",)


def test_every_source_says_where_its_data_comes_from():
    assert all(s.attribution.endswith("CC BY 4.0.") for s in SOURCES.values())


def test_protected_sites_carry_their_designation_and_ask_for_simplified_boundaries():
    feature = {
        "type": "Feature",
        "properties": {"SITECODE": "000006", "SITE_NAME": " Killyconny Bog SAC ", "URL": ""},
        "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
    }
    rows = SOURCES["sac"].transform({"features": [feature]})
    assert rows[0]["designation"] == "SAC"
    assert (rows[0]["site_code"], rows[0]["name"], rows[0]["url"]) == ("000006", "Killyconny Bog SAC", None)
    assert SOURCES["spa"].transform({"features": [feature]})[0]["designation"] == "SPA"
    assert all(SOURCES[n].max_offset == 0.0001 for n in ("sac", "spa", "nha"))
    assert SOURCES["counties"].max_offset is None
