-- Commencement notices: homes whose construction has started. Idempotent.
-- One row per residential notice (a phase of a scheme). No street, Eircode or
-- building names are kept; a project name only for notices of five homes or more.

create table if not exists dw.commencement (
    notice_number   text    primary key,
    local_authority text    not null,
    county          text    not null,             -- from the local authority
    submitted       date    not null,             -- when the notice reached the council
    commenced       date,                         -- the start date it gives
    expected_end    date,
    homes           integer,                      -- homes in this notice (phase)
    scheme_homes    integer,                      -- homes in the whole scheme
    homes_completed integer not null default 0,   -- from completion certificates
    planning_ref    text,
    project_name    text,
    location        geometry(Point, 2157) not null,
    settlement      text,                         -- CSO code of the containing settlement, if any
    snapshot_id     uuid    not null references dw.snapshot (id)
);
create index if not exists commencement_county_commenced on dw.commencement (county, commenced);
create index if not exists commencement_settlement on dw.commencement (settlement);
