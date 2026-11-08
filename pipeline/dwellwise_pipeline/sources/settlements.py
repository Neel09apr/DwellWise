"""Tailte Éireann / CSO settlement boundaries (2015, generalised 100 m). CC BY 4.0.

The layer has no county field. The loader assigns each settlement the county
that contains it, or the nearest one for the few that sit on the coastline
just outside every county polygon.
"""

import json

from ..names import name_key
from .base import Source

LAYER = (
    "https://services-eu1.arcgis.com/FH5XCsx8rYXqnjF5/arcgis/rest/services/"
    "Settlements_Generalised_100m/FeatureServer/0"
)


def transform(collection: dict) -> list[dict]:
    rows = []
    for f in collection["features"]:
        name = f["properties"]["SETTL_NAME"].strip()
        rows.append(
            {
                "code": str(f["properties"]["SETTLEMENT"]).strip(),
                "name": name,
                "name_key": name_key(name),
                "geometry": json.dumps(f["geometry"]),
            }
        )
    return rows


SOURCE = Source(
    name="settlements",
    layer_url=LAYER,
    out_fields=("SETTLEMENT", "SETTL_NAME"),
    order_by="OBJECTID_12",
    required_fields=("SETTLEMENT", "SETTL_NAME"),
    min_rows=800,
    table="settlement",
    attribution="© Tailte Éireann. CC BY 4.0.",
    transform=transform,
)
