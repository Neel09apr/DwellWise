# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Primary: people preparing a small housing scheme in Ireland (a self-builder, a
small developer, an architect's client) before their first pre-planning meeting
with the council. They arrive knowing a town or a county and want to know what
the public record already says about it: what was granted or refused there,
what is being built, which protected sites are close, what homes sell for, and
whether the wastewater plant has spare capacity.

Secondary: people reviewing DwellWise as a portfolio project for Cloud, SRE and
Platform roles. They judge the product by how well it serves the primary user;
the platform work is shown elsewhere (README, docs, the live service), not by
bending the product UI toward them (confirmed 26 November 2026).

## Product Purpose

An evidence-backed pre-planning brief for a town, built only from public data,
with every figure traceable to its source and capture date. Success: the user
walks into the meeting knowing the town's planning and building record, and
which questions remain open.

## Positioning

The only place that puts one Irish town's planning precedents, construction
starts, protected sites and area sale prices side by side, refreshed nightly,
each with its source, and that compares a county's towns on those same facts.
It describes towns, never a site, and never predicts a planning outcome.

## Operating Context

- Hierarchy: Ireland > county > settlement (CSO town) > brief, with breadcrumbs.
- Surfaces today: Ireland page (search, national planning activity, construction
  starts, map of schemes, sale prices, counties); county page (the same plus
  "Towns compared", the A to Z of its towns); the brief (wastewater register
  link, planning precedents, protected sites, sale prices, sources); the cost
  estimate (`/costs`, from the user's own figures); the assistant (a short
  conversation that answers only with checked figures and can return a
  code-ranked shortlist of towns).
- Data lags: the national planning dataset runs about ten days behind;
  commencement notices are fresh to the previous night; four councils rarely
  state unit counts.
- Used at a desk while preparing for a meeting; briefs may be printed or shared.

## Capabilities and Constraints

- Facts come from code, never from the model; the assistant only rephrases and
  every number it shows is checked against the data.
- Wastewater capacity cannot be republished (the register's terms): the brief
  links to the county register and nothing ranks or filters on capacity.
  "Nearby alternatives" waits on the same licence.
- Out of scope: planning advice or likelihood of permission, valuing a site or
  property, individual sale addresses, applicant names, flood data, user
  accounts (drafts stay in the browser), any paid service.
- Domain wording: "no spare capacity" means a Confirmation of Feasibility and
  possibly an upgrade, not a refusal; settlement evidence describes the town,
  never the user's site; "residential" is not "housing".
- Runs on free tiers only ($0 a month); the site must work with the assistant
  switched off.

## Brand Commitments

- The name DwellWise and its mark (`app/web/public/mark-small.svg`): two hollow half-roof bands meeting at the
  ridge, green (#0E4A2F) left and gold (#C99A2E) right, coded as SVG, with the wordmark "DwellWise" in
  mixed case in the green (owner's logo, 26 November 2026). Its colours belong to the logo only.
- An honest, plain-English, evidence-first voice that states sources and gaps.
- Nothing in the current visual look is binding: fonts, colours and layout are
  open for the UI revisit (confirmed 26 November 2026). CLAUDE.md rule 10 is to
  be rewritten from the new DESIGN.md.

## Evidence on Hand

- Live data for every county and town (planning applications from 2020,
  commencement notices, protected sites, CSO sale prices), served by the API.
- No testimonials, customers, usage figures or press exist; none may be invented.

## Product Principles

1. Evidence before interpretation: show the record and its source, then any summary.
2. Describe the town, never the site; never imply a planning outcome.
3. Say what is missing as clearly as what is known (lags, unstated units, capacity).
4. Every view works without the assistant; the assistant adds, never replaces.

## Accessibility & Inclusion

WCAG 2.2 AA: keyboard reach to every control and scrolling table, visible focus,
contrast at least 4.5:1 for text, charts with a table alternative, no meaning
carried by colour alone.
