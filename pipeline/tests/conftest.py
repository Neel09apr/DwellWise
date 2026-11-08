"""Small synthetic boundaries near Ireland, in WGS84 like the service returns."""

import pytest


def square(west: float, south: float, east: float, north: float) -> dict:
    return {
        "type": "Polygon",
        "coordinates": [[[west, south], [east, south], [east, north], [west, north], [west, south]]],
    }


def collection(features: list[dict]) -> dict:
    return {"type": "FeatureCollection", "features": features}


@pytest.fixture
def counties() -> dict:
    # A gap between the two counties (-9.2 to -9.0) holds a "coastal" settlement.
    return collection(
        [
            {
                "type": "Feature",
                "properties": {"COUNTY": "Cork "},
                "geometry": square(-9.0, 51.8, -8.0, 52.2),
            },
            {
                "type": "Feature",
                "properties": {"COUNTY": "KERRY"},
                "geometry": square(-10.0, 51.8, -9.2, 52.2),
            },
        ]
    )


@pytest.fixture
def settlements() -> dict:
    return collection(
        [
            {
                "type": "Feature",
                "properties": {"SETTLEMENT": 1001, "SETTL_NAME": "Baile Átha Fhirdhia"},
                "geometry": square(-8.6, 51.9, -8.5, 52.0),
            },
            {
                "type": "Feature",
                "properties": {"SETTLEMENT": "1002", "SETTL_NAME": "Carrick-On-Shannon"},
                "geometry": square(-9.18, 52.0, -9.15, 52.05),
            },
        ]
    )
