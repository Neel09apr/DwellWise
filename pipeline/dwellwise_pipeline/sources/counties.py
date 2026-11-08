"""Tailte Éireann county boundaries (2019, generalised 20 m). CC BY 4.0."""

import json

from .base import Source

LAYER = (
    "https://services-eu1.arcgis.com/FH5XCsx8rYXqnjF5/arcgis/rest/services/"
    "Counties___OSi_National_Statutory_Boundaries___Generalised_20m/FeatureServer/0"
)


def transform(collection: dict) -> list[dict]:
    return [
        {"name": f["properties"]["COUNTY"].strip().upper(), "geometry": json.dumps(f["geometry"])}
        for f in collection["features"]
    ]


SOURCE = Source(
    name="counties",
    layer_url=LAYER,
    out_fields=("COUNTY",),
    order_by="ESRI_OID",
    required_fields=("COUNTY",),
    min_rows=26,
    table="county",
    attribution="© Tailte Éireann. CC BY 4.0.",
    transform=transform,
)
