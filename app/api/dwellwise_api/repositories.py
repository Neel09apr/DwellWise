"""SQL only. Every value is a bound parameter."""

from __future__ import annotations

from datetime import date

from psycopg.rows import dict_row


def list_counties(conn) -> list[dict]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            select c.name, count(s.code)::int as settlements
            from dw.county c left join dw.settlement s on s.county = c.name
            group by c.name order by c.name
            """
        )
        return cur.fetchall()


def county_exists(conn, name: str) -> bool:
    with conn.cursor() as cur:
        cur.execute("select 1 from dw.county where name = %s", (name,))
        return cur.fetchone() is not None


def county_settlements(conn, name: str) -> list[dict]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute("select code, name, county from dw.settlement where county = %s order by name", (name,))
        return cur.fetchall()


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


def application_stats_data(conn, county: str | None, residential: bool | None, start, end) -> dict:
    """Everything the stats endpoint needs, in one round trip.

    Returns the county names, the counts of applications received in
    [start, end) per county, month and decision class, and when planning last
    loaded. One query matters here: Render (Frankfurt) to Supabase (Ireland)
    costs about 25 ms per round trip.
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            with counts as (
                select county, date_trunc('month', received)::date as month, decision_class,
                       count(*)::int as n
                from dw.planning_application
                where received >= %(start)s and received < %(end)s
                  and (%(county)s::text is null or county = %(county)s)
                  and (%(residential)s::boolean is null or residential = %(residential)s)
                group by 1, 2, 3
            )
            select
                (select coalesce(json_agg(name order by name), '[]') from dw.county) as counties,
                (select coalesce(json_agg(json_build_object(
                    'county', county, 'month', month, 'decision_class', decision_class, 'n', n)), '[]')
                 from counts) as rows,
                (select max(fetched_at) from dw.snapshot where source = 'planning' and status = 'loaded')
                    as captured_at
            """,
            {"start": start, "end": end, "county": county, "residential": residential},
        )
        data = cur.fetchone()
    rows = [{**r, "month": date.fromisoformat(r["month"])} for r in data["rows"]]
    return {"counties": data["counties"], "rows": rows, "captured_at": data["captured_at"]}
