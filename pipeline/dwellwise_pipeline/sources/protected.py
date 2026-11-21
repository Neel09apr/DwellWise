"""NPWS designated sites: SACs, SPAs and NHAs, one source per layer. CC BY 4.0.

The service is the one npws.ie links from its boundary-data page. Boundaries
are asked for simplified to about 10 m (maxAllowableOffset in degrees): the
full SPA layer is 47 MB, simplified it is 4 MB, and the brief only bands
distances at 1 km and 5 km. Proposed NHAs (layer 1) are not in v1.
"""

import json
from functools import partial

from .base import Source

SERVICE = (
    "https://services-eu1.arcgis.com/Jhij7i46ouO8Cc0N/arcgis/rest/services/NPWSDesignatedAreas/FeatureServer"
)
MAX_OFFSET = 0.0001  # degrees: about 7 m east-west and 11 m north-south in Ireland
ATTRIBUTION = (
    "Protected sites: National Parks and Wildlife Service, Department of Housing, "
    "Local Government and Heritage. CC BY 4.0."
)


def transform(designation: str, collection: dict) -> list[dict]:
    return [
        {
            "designation": designation,
            "site_code": str(f["properties"]["SITECODE"]).strip(),
            "name": f["properties"]["SITE_NAME"].strip(),
            "url": (f["properties"].get("URL") or "").strip() or None,
            "geometry": json.dumps(f["geometry"]),
        }
        for f in collection["features"]
    ]


def _source(name: str, layer: int, designation: str, min_rows: int) -> Source:
    return Source(
        name=name,
        layer_url=f"{SERVICE}/{layer}",
        out_fields=("SITECODE", "SITE_NAME", "URL"),
        order_by="OBJECTID",
        required_fields=("SITECODE", "SITE_NAME"),
        min_rows=min_rows,
        table="protected_site",
        attribution=ATTRIBUTION,
        transform=partial(transform, designation),
        max_offset=MAX_OFFSET,
    )


# Live counts on 21 Nov 2026: 433 SAC, 202 SPA, 171 NHA features.
SAC = _source("sac", 3, "SAC", 400)
SPA = _source("spa", 0, "SPA", 180)
NHA = _source("nha", 2, "NHA", 150)
