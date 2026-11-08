"""Load transformed rows into the live tables in one transaction.

Rows go into a temporary staging table first; the live table is replaced from
it only after every row has been accepted. Readers keep seeing the previous
data until the transaction commits, and a failure leaves it untouched.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

# GeoJSON arrives in WGS84; store Irish Transverse Mercator, repaired and as MultiPolygon.
GEOM = (
    "ST_Multi(ST_CollectionExtract(ST_MakeValid("
    "ST_Transform(ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326), 2157)), 3))"
)

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"


class LoadError(RuntimeError):
    """The load could not run (for example, a dependency is missing)."""


def migrate(conn) -> None:
    """Apply every SQL file in order. Each file is idempotent."""
    for path in sorted(SQL_DIR.glob("*.sql")):
        with conn.transaction():
            conn.execute(path.read_text(encoding="utf-8"))


def load_counties(cur, rows: list[dict], snapshot_id: str) -> dict:
    cur.execute("create temp table stage (like dw.county) on commit drop")
    cur.executemany(
        # GEOM is a constant; every value is a bound parameter.
        f"insert into stage (name, boundary, snapshot_id) values (%s, {GEOM}, %s)",  # noqa: S608
        [(r["name"], r["geometry"], snapshot_id) for r in rows],
    )
    cur.execute("delete from dw.county")
    cur.execute("insert into dw.county select * from stage")
    return {}


def load_settlements(cur, rows: list[dict], snapshot_id: str) -> dict:
    cur.execute("select count(*) from dw.county")
    if cur.fetchone()[0] == 0:
        raise LoadError(
            "load counties before settlements: the county of each settlement is derived from them"
        )
    cur.execute("create temp table stage (like dw.settlement) on commit drop")
    cur.executemany(
        f"insert into stage (code, name, name_key, county, boundary, snapshot_id) "  # noqa: S608 - constant GEOM
        f"values (%s, %s, %s, null, {GEOM}, %s)",
        [(r["code"], r["name"], r["name_key"], r["geometry"], snapshot_id) for r in rows],
    )
    # A point on the surface is always inside the polygon, unlike a centroid.
    cur.execute(
        "update stage s set county = c.name from dw.county c "
        "where ST_Contains(c.boundary, ST_PointOnSurface(s.boundary))"
    )
    cur.execute(
        "update stage s set county = "
        "(select c.name from dw.county c order by c.boundary <-> s.boundary limit 1) "
        "where s.county is null"
    )
    nearest = cur.rowcount
    cur.execute("delete from dw.settlement")
    cur.execute("insert into dw.settlement select * from stage")
    return {"county_by_nearest": nearest}


LOADERS: dict[str, Callable[..., dict]] = {"county": load_counties, "settlement": load_settlements}
