-- Planning applications from the national dataset. Idempotent.
-- No applicant names or addresses, ever: they are never fetched, and the
-- pipeline rejects a collection that carries them.

create table if not exists dw.planning_application (
    authority          text    not null,             -- planning authority, as published
    application_number text    not null,
    received           date    not null,
    decided            date,
    decision           text,                         -- the council's own wording, trimmed
    decision_class     text    not null
        check (decision_class in ('granted', 'refused', 'pending', 'withdrawn', 'other')),
    county             text    not null,             -- from the authority
    units_stated       integer,
    residential        boolean not null,             -- states dwellings: units or a one-off house
    location           geometry(Point, 2157) not null,
    settlement         text,                         -- CSO code of the containing settlement, if any
    snapshot_id        uuid    not null references dw.snapshot (id),
    primary key (authority, application_number)
);
create index if not exists planning_county_received on dw.planning_application (county, received);
create index if not exists planning_settlement on dw.planning_application (settlement);
create index if not exists planning_location_gix on dw.planning_application using gist (location);
