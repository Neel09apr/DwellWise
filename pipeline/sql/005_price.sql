-- CSO sale prices per area and month, and the routing key that ties a town to its
-- price area. Idempotent.

create table if not exists dw.price (
    kind        text    not null check (kind in ('eircode', 'region')),
    code        text    not null,      -- routing key (C15) or CSO area code ('-' is all of Ireland)
    name        text    not null,      -- as the CSO labels it: "Navan", "Cork County"
    month       date    not null,      -- first day of the month of the sale (deed executed)
    status      text    not null check (status in ('all', 'new')),
    sales       integer,               -- null where the CSO suppresses a small count
    median      integer,               -- euro
    mean        integer,               -- euro
    snapshot_id uuid    not null references dw.snapshot (id),
    primary key (kind, code, month, status)
);

-- First three characters of a commencement notice's Eircode, never the full code.
alter table dw.commencement add column if not exists routing_key text;
create index if not exists commencement_settlement_routing on dw.commencement (settlement, routing_key);
