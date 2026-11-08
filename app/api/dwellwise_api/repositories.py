"""SQL only. Every value is a bound parameter."""

from __future__ import annotations

from psycopg.rows import dict_row


def search_settlements(conn, key: str, county: str | None, limit: int) -> list[dict]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            select code, name, county
            from dw.settlement
            where name_key like %(contains)s
              and (%(county)s::text is null or county = %(county)s)
            order by name_key = %(key)s desc, name_key like %(prefix)s desc, length(name), name
            limit %(limit)s
            """,
            {"contains": f"%{key}%", "prefix": f"{key}%", "key": key, "county": county, "limit": limit},
        )
        return cur.fetchall()


def get_settlement(conn, code: str) -> dict | None:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            select code, name, county,
                   ST_Y(p) as latitude, ST_X(p) as longitude,
                   round((ST_Area(boundary) / 1e6)::numeric, 2)::float as area_km2
            from (
                select *, ST_Transform(ST_PointOnSurface(boundary), 4326) as p
                from dw.settlement where code = %s
            ) s
            """,
            (code,),
        )
        return cur.fetchone()


def loaded_sources(conn) -> dict[str, dict]:
    """Latest successful load per source, with its age in hours."""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            select source, max(fetched_at) as captured_at,
                   extract(epoch from now() - max(fetched_at)) / 3600 as age_hours
            from dw.snapshot where status = 'loaded'
            group by source
            """
        )
        return {row["source"]: row for row in cur.fetchall()}
