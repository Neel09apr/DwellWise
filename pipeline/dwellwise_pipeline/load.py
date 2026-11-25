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


def _stage(cur, name: str, columns: dict[str, str], rows: list[dict]) -> None:
    """Create a temporary staging table of these columns (dropped at commit) and COPY the rows in."""
    cur.execute(
        f"create temp table {name} ({', '.join(f'{c} {t}' for c, t in columns.items())}) on commit drop"
    )
    with cur.copy(f"copy {name} ({', '.join(columns)}) from stdin") as copy:
        for r in rows:
            copy.write_row(tuple(r[c] for c in columns))


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


PLANNING_COLUMNS = {
    "authority": "text", "application_number": "text", "received": "date", "decided": "date",
    "decision": "text", "decision_class": "text", "recognised": "boolean", "county": "text",
    "units_stated": "integer", "residential": "boolean", "geometry": "text",
}  # fmt: skip


def load_planning(cur, rows: list[dict], snapshot_id: str) -> dict:
    """COPY into staging (hundreds of thousands of rows), then swap in one statement.

    A repeated application number keeps its most recently received row. Each
    point gets the settlement that contains it, if any.
    """
    _stage(cur, "stage_planning", PLANNING_COLUMNS, rows)
    cur.execute("select count(*) filter (where not recognised) from stage_planning")
    unrecognised = cur.fetchone()[0]
    cur.execute("delete from dw.planning_application")
    cur.execute(
        "insert into dw.planning_application (authority, application_number, received, decided, decision, "
        "decision_class, county, units_stated, residential, location, settlement, snapshot_id) "
        "select p.authority, p.application_number, p.received, p.decided, p.decision, p.decision_class, "
        "p.county, p.units_stated, p.residential, p.location, "
        "(select s.code from dw.settlement s where ST_Contains(s.boundary, p.location) limit 1), %s "
        "from (select distinct on (authority, application_number) *, "
        "ST_Transform(ST_SetSRID(ST_GeomFromGeoJSON(geometry), 4326), 2157) as location "
        "from stage_planning order by authority, application_number, received desc) p",
        (snapshot_id,),
    )
    return {"duplicates_dropped": len(rows) - cur.rowcount, "decisions_unrecognised": unrecognised}


def load_protected(cur, rows: list[dict], snapshot_id: str) -> dict:
    """Replace one designation's sites. A site published as several features becomes one row."""
    designations = {r["designation"] for r in rows}
    if len(designations) != 1:
        raise LoadError(f"one designation per run, got {sorted(designations)}")
    cur.execute(
        "create temp table stage_protected (designation text, site_code text, name text, url text, "
        "boundary geometry(MultiPolygon, 2157)) on commit drop"
    )
    cur.executemany(
        f"insert into stage_protected values (%s, %s, %s, %s, {GEOM})",  # noqa: S608 - constant GEOM
        [(r["designation"], r["site_code"], r["name"], r["url"], r["geometry"]) for r in rows],
    )
    cur.execute("delete from dw.protected_site where designation = %s", (designations.pop(),))
    cur.execute(
        "insert into dw.protected_site (designation, site_code, name, url, boundary, snapshot_id) "
        "select designation, site_code, min(name), min(url), "
        "ST_Multi(ST_CollectionExtract(ST_Union(boundary), 3)), %s "
        "from stage_protected group by designation, site_code",
        (snapshot_id,),
    )
    return {"features_merged": len(rows) - cur.rowcount}


COMMENCEMENT_COLUMNS = {
    "notice_number": "text", "local_authority": "text", "county": "text", "submitted": "date",
    "commenced": "date", "expected_end": "date", "homes": "integer", "scheme_homes": "integer",
    "homes_completed": "integer", "planning_ref": "text", "project_name": "text", "routing_key": "text",
    "geometry": "text",
}  # fmt: skip


def load_commencements(cur, rows: list[dict], snapshot_id: str) -> dict:
    """COPY into staging, then replace the table, placing each notice in its settlement."""
    _stage(cur, "stage_commencement", COMMENCEMENT_COLUMNS, rows)
    cur.execute("delete from dw.commencement")
    cur.execute(
        "insert into dw.commencement (notice_number, local_authority, county, submitted, commenced, "
        "expected_end, homes, scheme_homes, homes_completed, planning_ref, project_name, routing_key, "
        "location, settlement, snapshot_id) "
        "select c.notice_number, c.local_authority, c.county, c.submitted, c.commenced, c.expected_end, "
        "c.homes, c.scheme_homes, c.homes_completed, c.planning_ref, c.project_name, c.routing_key, "
        "c.location, "
        "(select s.code from dw.settlement s where ST_Contains(s.boundary, c.location) limit 1), %s "
        "from (select *, ST_Transform(ST_SetSRID(ST_GeomFromGeoJSON(geometry), 4326), 2157) as location "
        "from stage_commencement) c",
        (snapshot_id,),
    )
    cur.execute("select count(*) filter (where settlement is not null) from dw.commencement")
    return {"in_a_settlement": cur.fetchone()[0]}


PRICE_COLUMNS = {
    "kind": "text", "code": "text", "name": "text", "month": "date", "status": "text",
    "sales": "integer", "median": "integer", "mean": "integer",
}  # fmt: skip


def load_prices(cur, rows: list[dict], snapshot_id: str) -> dict:
    """Replace the CSO price table: one row per area, month and dwelling status."""
    _stage(cur, "stage_price", PRICE_COLUMNS, rows)
    columns = ", ".join(PRICE_COLUMNS)
    cur.execute("delete from dw.price")
    cur.execute(
        f"insert into dw.price ({columns}, snapshot_id) select {columns}, %s from stage_price",  # noqa: S608 - constant columns
        (snapshot_id,),
    )
    return {}


LOADERS: dict[str, Callable[..., dict]] = {
    "county": load_counties,
    "settlement": load_settlements,
    "planning_application": load_planning,
    "protected_site": load_protected,
    "commencement": load_commencements,
    "price": load_prices,
}
