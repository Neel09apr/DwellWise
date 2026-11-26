"""SQL only. Every value is a bound parameter."""

from __future__ import annotations

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


def registered_sources(conn) -> list[dict]:
    """Every source the pipeline has registered, in its order, with its latest successful load.

    ``captured_at`` and ``age_hours`` are None for a source that has never loaded.
    An empty list when nothing is registered, including before the registry
    table exists (the pipeline creates it on its first run after a deploy).
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute("select to_regclass('dw.source') is not null as present")
        if not cur.fetchone()["present"]:
            return []
        cur.execute(
            """
            select s.name, s.attribution, l.captured_at,
                   extract(epoch from now() - l.captured_at) / 3600 as age_hours
            from dw.source s
            left join (
                select source, max(fetched_at) as captured_at from dw.snapshot
                where status = 'loaded' group by source
            ) l on l.source = s.name
            order by s.position, s.name
            """
        )
        return cur.fetchall()


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
    rows = [{**r, "month": r["month"][:7]} for r in data["rows"]]  # YYYY-MM, as Months labels them
    return {
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


def development_points(conn, county: str | None, min_homes: int, days: int, sparse_below: int) -> dict:
    """Schemes of at least ``min_homes`` homes on a map, in one round trip.

    Started: commencement notices with a start date in the last ``days`` days (or
    up to 60 days ahead, as notices are filed before work begins). Applied:
    planning applications received in the last ``days`` days that state as many
    units. Coordinates are WGS84, rounded to 4 decimals (about 10 m). Also the
    councils that state units on fewer than ``sparse_below`` percent of their
    applications: their schemes cannot be sized, so they are missing from the map.
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
                (select coalesce(json_agg(json_build_object(
                    'kind', kind, 'label', label, 'authority', authority, 'homes', homes, 'day', day,
                    'settlement', settlement, 'status', status, 'reference', reference,
                    'lng', round(ST_X(p)::numeric, 4), 'lat', round(ST_Y(p)::numeric, 4))
                    order by day desc), '[]') from points) as points,
                (select coalesce(json_agg(json_build_object('authority', authority, 'share', share)
                    order by authority), '[]') from (
                    select authority,
                           round(avg((units_stated is not null)::int) * 100)::int as share
                    from dw.planning_application
                    where received >= current_date - %(days)s
                      and (%(county)s::text is null or county = %(county)s)
                    group by authority) g
                 where share < %(sparse_below)s) as sparse_units
            """,
            {"county": county, "min_homes": min_homes, "days": days, "sparse_below": sparse_below},
        )
        return cur.fetchone()


def price_data(conn, county: str | None, settlement: str | None, since) -> dict:
    """Every candidate price area for a place, with its months since ``since``, in one round trip.

    Candidates: the Eircode routing key most of the town's commencement notices
    carry (with how many), the county's CSO areas (exact name, or "<county> ..."
    for counties split into city and county), and the national row ('-'). For a
    settlement, ``county`` is its own county (``Place`` supplies it).
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            with key as (
                select routing_key, count(*)::int as notices, (sum(count(*)) over ())::int as with_eircode
                from dw.commencement
                where %(settlement)s::text is not null and settlement = %(settlement)s
                  and routing_key is not null
                group by routing_key order by count(*) desc, routing_key limit 1
            )
            select
                (select row_to_json(key) from key) as key,
                (select max(fetched_at) from dw.snapshot where source = 'prices' and status = 'loaded')
                    as captured_at,
                (select coalesce(json_agg(p order by kind, code, month, status), '[]') from (
                    select kind, code, name, month, status, sales, median from dw.price
                    where month >= %(since)s and (
                        (kind = 'eircode' and code = (select routing_key from key))
                        or (kind = 'region' and (code = '-'
                            or upper(name) = %(county)s
                            or upper(name) like %(county)s || ' %%')))
                ) p) as rows
            """,
            {"county": county, "settlement": settlement, "since": since},
        )
        return cur.fetchone()


def shortlist_rows(
    conn, county: str, since, started_from, started_to, near_m: int, price_since
) -> list[dict]:
    """Every town in a county with its evidence columns, in one round trip (``shortlist`` ranks them)."""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            with towns as (
                select code, name, boundary from dw.settlement where county = %(county)s
            ), apps as (
                select settlement,
                       count(*) filter (where decision_class = 'granted')::int as granted,
                       count(*) filter (where decision_class = 'refused')::int as refused,
                       count(*) filter (where decision_class = 'pending')::int as pending
                from dw.planning_application
                where residential and received >= %(since)s and settlement in (select code from towns)
                group by settlement
            ), started as (
                select settlement, coalesce(sum(homes), 0)::int as homes from dw.commencement
                where commenced >= %(started_from)s and commenced < %(started_to)s
                  and settlement in (select code from towns)
                group by settlement
            ), keys as (  -- the routing key most of the town's notices carry, as /v1/prices chooses it
                select distinct on (settlement) settlement, routing_key from (
                    select settlement, routing_key, count(*) as n from dw.commencement
                    where routing_key is not null and settlement in (select code from towns)
                    group by 1, 2) k
                order by settlement, n desc, routing_key
            ), latest as (
                select distinct on (code) code, to_char(month, 'YYYY-MM') as month, median from dw.price
                where kind = 'eircode' and status = 'all' and median is not null and month >= %(price_since)s
                order by code, month desc
            ), near as (
                select t.code, count(*)::int as n from towns t
                join dw.protected_site ps on ST_DWithin(ps.boundary, t.boundary, %(near)s)
                group by t.code
            )
            select t.code, t.name,
                   coalesce(a.granted, 0) as granted, coalesce(a.refused, 0) as refused,
                   coalesce(a.pending, 0) as pending, coalesce(s.homes, 0) as homes_started,
                   coalesce(n.n, 0) as protected_within_1km,
                   k.routing_key as price_area, l.median as median_price, l.month as price_month
            from towns t
            left join apps a on a.settlement = t.code
            left join started s on s.settlement = t.code
            left join near n on n.code = t.code
            left join keys k on k.settlement = t.code
            left join latest l on l.code = k.routing_key
            """,
            {
                "county": county,
                "since": since,
                "started_from": started_from,
                "started_to": started_to,
                "near": near_m,
                "price_since": price_since,
            },  # fmt: skip
        )
        return cur.fetchall()
