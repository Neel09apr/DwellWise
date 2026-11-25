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
                    as captured_at,
                (select max(received) from dw.planning_application
                 where (%(county)s::text is null or county = %(county)s)
                   and (%(residential)s::boolean is null or residential = %(residential)s))
                    as newest_received
            """,
            {"start": start, "end": end, "county": county, "residential": residential},
        )
        data = cur.fetchone()
    rows = [{**r, "month": date.fromisoformat(r["month"])} for r in data["rows"]]
    return {
        "counties": data["counties"],
        "rows": rows,
        "captured_at": data["captured_at"],
        "newest_received": data["newest_received"],
    }


def commencement_data(conn, county: str | None, settlement: str | None, start, end, named_from: int) -> dict:
    """Everything the commencements endpoint needs, in one round trip.

    Homes started per month (by commencement date) in [start, end), notices
    received in the week before the last capture, and the newest named schemes
    (at least ``named_from`` homes; smaller notices are never listed).
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            with scope as (
                select c.*, s.name as settlement_name from dw.commencement c
                left join dw.settlement s on s.code = c.settlement
                where (%(county)s::text is null or c.county = %(county)s)
                  and (%(settlement)s::text is null or c.settlement = %(settlement)s)
            ), captured as (
                select max(fetched_at) as at from dw.snapshot
                where source = 'commencements' and status = 'loaded'
            )
            select
                (%(county)s::text is null or exists (select 1 from dw.county where name = %(county)s))
                    as county_known,
                (%(settlement)s::text is null
                 or exists (select 1 from dw.settlement where code = %(settlement)s))
                    as settlement_known,
                (select at from captured) as captured_at,
                (select max(submitted) from scope) as newest_submitted,
                (select coalesce(json_agg(m order by m.month), '[]') from (
                    select to_char(date_trunc('month', commenced), 'YYYY-MM') as month,
                           count(*)::int as notices, coalesce(sum(homes), 0)::int as homes
                    from scope where commenced >= %(start)s and commenced < %(end)s group by 1) m) as months,
                (select json_build_object('notices', count(*), 'homes', coalesce(sum(homes), 0))
                 from scope, captured
                 where submitted > (captured.at at time zone 'UTC')::date - 7) as last_7_days,
                (select coalesce(json_agg(r), '[]') from (
                    select notice_number, project_name, settlement_name as settlement, county,
                           local_authority, homes, scheme_homes, commenced, expected_end, planning_ref
                    from scope where homes >= %(named_from)s
                    order by submitted desc, notice_number limit 10) r) as recent_schemes
            """,
            {
                "county": county,
                "settlement": settlement,
                "start": start,
                "end": end,
                "named_from": named_from,
            },
        )
        return cur.fetchone()


def settlement_brief(conn, code: str, since, limit: int, radius_m: int) -> dict:
    """Every live section of one settlement's brief, in one round trip."""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            with apps as (
                select authority, application_number, received, decided, decision, decision_class,
                       units_stated, residential
                from dw.planning_application
                where settlement = %(code)s and received >= %(since)s
            )
            select
                exists (select 1 from dw.settlement where code = %(code)s) as found,
                (select coalesce(json_object_agg(decision_class, n), '{}')
                 from (select decision_class, count(*) as n from apps where residential group by 1) c)
                    as residential,
                (select count(*)::int from apps) as all_total,
                (select coalesce(json_agg(r), '[]') from (
                    select authority, application_number, received, decided, decision, decision_class,
                           units_stated
                    from apps where residential
                    order by received desc, application_number
                    limit %(limit)s) r) as recent,
                (select max(fetched_at) from dw.snapshot where source = 'planning' and status = 'loaded')
                    as captured_at,
                (select coalesce(json_agg(p order by p.distance_m, p.designation, p.site_code), '[]') from (
                    select ps.designation, ps.site_code, ps.name, ps.url,
                           round(ST_Distance(ps.boundary, s.boundary))::int as distance_m
                    from dw.settlement s
                    join dw.protected_site ps on ST_DWithin(ps.boundary, s.boundary, %(radius)s)
                    where s.code = %(code)s) p) as protected,
                -- the oldest of the three designations' latest loads: the section is as old as that
                (select min(latest) from (
                    select max(fetched_at) as latest from dw.snapshot
                    where source in ('sac', 'spa', 'nha') and status = 'loaded' group by source) l)
                    as protected_captured_at
            """,
            {"code": code, "since": since, "limit": limit, "radius": radius_m},
        )
        return cur.fetchone()


def development_points(conn, county: str | None, min_homes: int, days: int) -> dict:
    """Schemes of at least ``min_homes`` homes on a map, in one round trip.

    Started: commencement notices with a start date in the last ``days`` days (or
    up to 60 days ahead, as notices are filed before work begins). Applied:
    planning applications received in the last ``days`` days that state as many
    units. Coordinates are WGS84, rounded to 4 decimals (about 10 m).
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            with points as (
                select 'started' as kind, coalesce(c.project_name, 'Unnamed scheme') as label,
                       c.local_authority as authority, c.homes, c.commenced as day,
                       s.name as settlement, null::text as status, c.planning_ref as reference,
                       ST_Transform(c.location, 4326) as p
                from dw.commencement c left join dw.settlement s on s.code = c.settlement
                where c.homes >= %(min_homes)s
                  and c.commenced between current_date - %(days)s and current_date + 60
                  and (%(county)s::text is null or c.county = %(county)s)
                union all
                select 'applied', null, a.authority, a.units_stated, a.received,
                       s.name, a.decision_class, a.application_number,
                       ST_Transform(a.location, 4326)
                from dw.planning_application a left join dw.settlement s on s.code = a.settlement
                where a.units_stated >= %(min_homes)s
                  and a.received >= current_date - %(days)s
                  and (%(county)s::text is null or a.county = %(county)s)
            )
            select
                (%(county)s::text is null or exists (select 1 from dw.county where name = %(county)s))
                    as county_known,
                (select coalesce(json_agg(json_build_object(
                    'kind', kind, 'label', label, 'authority', authority, 'homes', homes, 'day', day,
                    'settlement', settlement, 'status', status, 'reference', reference,
                    'lng', round(ST_X(p)::numeric, 4), 'lat', round(ST_Y(p)::numeric, 4))
                    order by day desc), '[]') from points) as points
            """,
            {"county": county, "min_homes": min_homes, "days": days},
        )
        return cur.fetchone()
