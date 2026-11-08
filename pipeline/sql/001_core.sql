-- Core tables for the rebuilt pipeline. Idempotent: safe to run on every deploy.
-- Lives in its own schema so it can sit beside older tables during the move.

create extension if not exists postgis;
create schema if not exists dw;

-- One row per pipeline run per source: what was fetched, where the raw copy
-- is, and what happened to it.
create table if not exists dw.snapshot (
    id          uuid primary key,
    source      text        not null,
    fetched_at  timestamptz not null,
    raw_uri     text        not null,
    sha256      text        not null,
    rows_loaded integer,
    status      text        not null check (status in ('loaded', 'rejected', 'failed')),
    detail      text
);
create index if not exists snapshot_source_time on dw.snapshot (source, fetched_at desc);

create table if not exists dw.county (
    name        text primary key,                    -- as published, e.g. CORK
    boundary    geometry(MultiPolygon, 2157) not null,
    snapshot_id uuid not null references dw.snapshot (id)
);
create index if not exists county_boundary_gix on dw.county using gist (boundary);

create table if not exists dw.settlement (
    code        text primary key,                    -- CSO settlement code
    name        text not null,
    name_key    text not null,                       -- see names.name_key
    county      text,                                -- derived spatially at load
    boundary    geometry(MultiPolygon, 2157) not null,
    snapshot_id uuid not null references dw.snapshot (id)
);
create index if not exists settlement_boundary_gix on dw.settlement using gist (boundary);
create index if not exists settlement_name_county on dw.settlement (name_key, county);
