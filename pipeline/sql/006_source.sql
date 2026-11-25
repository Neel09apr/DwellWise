-- The source registry: every source the pipeline runs, declared once in
-- dwellwise_pipeline/sources and registered here at the start of each run, so the
-- API learns which sources exist (for /ready and a settlement's source list) from
-- the database instead of keeping its own lists. Idempotent.
-- Retiring a source: remove it from SOURCES and delete its row in a migration,
-- or /ready will report it stale.

create table if not exists dw.source (
    name          text        primary key,
    attribution   text        not null,
    position      integer     not null,   -- order in SOURCES: run order, dependency order, display order
    registered_at timestamptz not null default now()
);
