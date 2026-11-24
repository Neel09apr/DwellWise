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


PLANNING_COLUMNS = (
    "authority", "application_number", "received", "decided", "decision", "decision_class",
    "recognised", "county", "units_stated", "residential", "geometry",
)  # fmt: skip


def load_planning(cur, rows: list[dict], snapshot_id: str) -> dict:
    """COPY into staging (hundreds of thousands of rows), then swap in one statement.

    A repeated application number keeps its most recently received row. Each
    point gets the settlement that contains it, if any.
    """
    cur.execute("select count(*) from dw.settlement")
    if cur.fetchone()[0] == 0:
        raise LoadError("load settlements before planning: each application is placed in one")
    cur.execute(
        "create temp table stage_planning (authority text, application_number text, received date, "
        "decided date, decision text, decision_class text, recognised boolean, county text, "
        "units_stated integer, residential boolean, geometry text) on commit drop"
    )
    with cur.copy(f"copy stage_planning ({', '.join(PLANNING_COLUMNS)}) from stdin") as copy:
        for r in rows:
            copy.write_row(tuple(r[c] for c in PLANNING_COLUMNS))
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


COMMENCEMENT_COLUMNS = (
    "notice_number", "local_authority", "county", "submitted", "commenced", "expected_end",
    "homes", "scheme_homes", "homes_completed", "planning_ref", "project_name", "geometry",
)  # fmt: skip


def load_commencements(cur, rows: list[dict], snapshot_id: str) -> dict:
    """COPY into staging, then replace the table, placing each notice in its settlement."""
    cur.execute("select count(*) from dw.settlement")
    if cur.fetchone()[0] == 0:
        raise LoadError("load settlements before commencements: each notice is placed in one")
    cur.execute(
        "create temp table stage_commencement (notice_number text, local_authority text, county text, "
        "submitted date, commenced date, expected_end date, homes integer, scheme_homes integer, "
        "homes_completed integer, planning_ref text, project_name text, geometry text) on commit drop"
    )
    with cur.copy(f"copy stage_commencement ({', '.join(COMMENCEMENT_COLUMNS)}) from stdin") as copy:
        for r in rows:
            copy.write_row(tuple(r[c] for c in COMMENCEMENT_COLUMNS))
    cur.execute("delete from dw.commencement")
    cur.execute(
        "insert into dw.commencement (notice_number, local_authority, county, submitted, commenced, "
        "expected_end, homes, scheme_homes, homes_completed, planning_ref, project_name, location, "
        "settlement, snapshot_id) "
        "select c.notice_number, c.local_authority, c.county, c.submitted, c.commenced, c.expected_end, "
        "c.homes, c.scheme_homes, c.homes_completed, c.planning_ref, c.project_name, c.location, "
        "(select s.code from dw.settlement s where ST_Contains(s.boundary, c.location) limit 1), %s "
        "from (select *, ST_Transform(ST_SetSRID(ST_GeomFromGeoJSON(geometry), 4326), 2157) as location "
        "from stage_commencement) c",
        (snapshot_id,),
    )
    cur.execute("select count(*) filter (where settlement is not null) from dw.commencement")
    return {"in_a_settlement": cur.fetchone()[0]}


LOADERS: dict[str, Callable[..., dict]] = {
    "county": load_counties,
    "settlement": load_settlements,
    "planning_application": load_planning,
    "protected_site": load_protected,
    "commencement": load_commencements,
}
