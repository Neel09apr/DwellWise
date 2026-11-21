-- NPWS protected sites (SAC, SPA, NHA). Idempotent.
-- An NHA can share its site code with a SAC, so the key is the pair.

create table if not exists dw.protected_site (
    designation text not null check (designation in ('SAC', 'SPA', 'NHA')),
    site_code   text not null,
    name        text not null,
    url         text,                                  -- the site's NPWS page
    boundary    geometry(MultiPolygon, 2157) not null, -- simplified to about 10 m
    snapshot_id uuid not null references dw.snapshot (id),
    primary key (designation, site_code)
);
create index if not exists protected_site_boundary_gix on dw.protected_site using gist (boundary);
