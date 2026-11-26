"""Seed the database tests through the pipeline's own loaders (pytest puts the pipeline on the path).

Each seed registers its source, records a loaded snapshot and runs the source's
loader, as a nightly run does after validation: the loader, not the test,
assigns each settlement its county and places applications and notices in
their town.
"""

import json
import uuid

from dwellwise_pipeline.load import LOADERS
from dwellwise_pipeline.run import register
from dwellwise_pipeline.sources import SOURCES


def box(west: float, south: float, east: float, north: float) -> str:
    ring = [[west, south], [east, south], [east, north], [west, north], [west, south]]
    return json.dumps({"type": "Polygon", "coordinates": [ring]})


def point(lng: float, lat: float) -> str:
    return json.dumps({"type": "Point", "coordinates": [lng, lat]})


def seed(conn, name: str, rows: list[dict]) -> str:
    """Load transformed rows for one source; returns the snapshot id."""
    source = SOURCES[name]
    snapshot = str(uuid.uuid4())
    with conn.transaction():
        register(conn, source)
        conn.execute(
            "insert into dw.snapshot (id, source, fetched_at, raw_uri, sha256, rows_loaded, status) "
            "values (%s, %s, now(), 'test://', 'x', %s, 'loaded')",
            (snapshot, name, len(rows)),
        )
        with conn.cursor() as cur:
            LOADERS[source.table](cur, rows, snapshot)
    return snapshot
