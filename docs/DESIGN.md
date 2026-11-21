# DwellWise system design

Status: **draft for review** · Owner: Neel Sawant · Last updated: 8 November 2026

## 1. Problem

Someone planning a small housing scheme in Ireland (a self-builder, a small
developer, an architect's client) walks into their first meeting with the
planning authority without knowing what the public record already says about
the town: whether the wastewater plant has spare capacity, what was granted or
refused nearby, which protected sites are close, and which nearby towns could
take the homes instead.

That evidence is public but scattered across registers, map services and PDFs.
DwellWise gathers it into one **pre-planning brief** the user can edit, check
and print.

## 2. Goals and non-goals (v1)

**Goals**

- A brief for a chosen settlement and proposal size, built from public data.
- A national view of planning activity: how many applications were granted,
  refused or are still pending, across Ireland and per county, refreshed nightly.
- Every fact traceable to its source and the date that source was captured.
- Runs at **$0/month** on free tiers, with no account that can bill.
- Operated like a production service: infrastructure as code, scanned
  delivery, monitoring with service-level objectives, runbooks.

**Non-goals**

- Planning advice or a likelihood of permission. The brief describes the
  town, never the user's site, and says so.
- Flood risk. The national flood maps are licensed CC-BY-NC-ND; no flood
  data is fetched or shown without written permission from the OPW.
- Applicant names or addresses. They are never fetched.
- User accounts in v1 (drafts stay in the browser; accounts are a later
  milestone).

## 3. Requirements

### Functional

| ID | The user can… |
|---|---|
| F1 | search for a settlement by name and county |
| F2 | enter a proposal: number of homes, houses or apartments |
| F3 | see wastewater capacity status for the settlement, in the register's own words, with the register edition date |
| F4 | see recent residential planning applications in the settlement and their decisions |
| F5 | see protected sites (SAC, SPA, NHA) within 1 km and 5 km |
| F6 | see nearby settlements with spare capacity, by distance |
| F7 | read an optional plain-English summary written over those facts |
| F8 | edit the brief, keep it in the browser, and print or export it |
| F9 | see planning activity for Ireland and each county: applications granted, refused and pending, by month, with the date the data was captured |

### Non-functional

| Area | Target |
|---|---|
| Availability | 99.0% of external health probes succeed per month (see §9 on free-tier cold starts) |
| Latency | Brief API p95 under 800 ms when warm |
| Freshness | Every source refreshed by a successful nightly run at least once in the last 48 hours |
| Correctness | Facts come from SQL and code, never from the AI step; the AI may only rephrase facts it is given |
| Cost | $0.00/month: free tiers only, no account that can bill |
| Security | No long-lived cloud keys; least-privilege roles; every pull request scanned |

## 4. Architecture

```mermaid
flowchart LR
  user["Browser<br/>React workspace"] -->|HTTPS| api["API<br/>FastAPI on Render"]
  api --> db[("Postgres + PostGIS<br/>Supabase")]
  api -.->|"optional summary"| llm["LLM API<br/>Gemini free tier"]

  subgraph gha["GitHub Actions"]
    sched["Schedule<br/>nightly"] --> fn["Pipeline container"]
  end
  fn --> raw["Supabase Storage<br/>raw snapshots (S3 API)"]
  fn --> obs

  sources["Public sources<br/>registers · planning API · boundaries · protected sites"] --> fn
  fn -->|"validated load"| db

  probe["Uptime probe<br/>status page"] --> api
  api --> obs["Grafana Cloud / Sentry"]
```

| Component | Responsibility | Runs on |
|---|---|---|
| Web (`app/web`) | The workspace: search, proposal, brief, edit, print | Static files served by the API container |
| API (`app/api`) | Read-only queries that assemble a brief; optional summary; health and metrics | Render free web service (Docker) |
| Database | Settlements, capacity, applications, protected sites, snapshot log; PostGIS for spatial joins | Supabase free (500 MB) |
| Pipeline (`pipeline/`) | Fetch each source, store the raw file, validate, transform, load | Scheduled GitHub Actions job running the pipeline container, nightly |
| Raw store | Dated, immutable copies of every fetched file | Supabase Storage bucket through its S3-compatible API |
| Infrastructure (`terraform/`) | Terraform for Render, Supabase and GitHub settings, applied by CI; the AWS modules are kept, to be tested against the Floci emulator, never deployed | GitHub Actions |

**Why this split.** The API only reads, so it can scale and fail
independently of ingestion. The pipeline is the only writer, so every change
to the data is logged against a run and can be replayed from the raw store.

## 5. Data model

```mermaid
erDiagram
  settlement ||--o{ capacity_status : has
  settlement ||--o{ planning_application : contains
  settlement }o--o{ protected_site : near
  snapshot ||--o{ capacity_status : loaded_by
  snapshot ||--o{ planning_application : loaded_by

  settlement {
    int id PK
    text name
    text county
    text name_key "normalised: lower case, letters only"
    geometry boundary "EPSG:2157"
  }
  capacity_status {
    int settlement_id FK
    text plant
    text status "NO SPARE CAPACITY | LIMITED CAPACITY | SPARE CAPACITY"
    date edition_date
    uuid snapshot_id FK
  }
  planning_application {
    text authority PK
    text application_number PK
    date received
    text decision
    text decision_class "granted | refused | pending | withdrawn | other"
    date decided
    text county
    int units_stated
    bool residential
    geometry location "EPSG:2157"
    text settlement "CSO code of the containing settlement, if any"
    uuid snapshot_id FK
  }
  protected_site {
    text designation PK "SAC | SPA | NHA"
    text site_code PK "an NHA can share its code with a SAC"
    text name
    text url "the site's NPWS page"
    geometry boundary "EPSG:2157, simplified to about 10 m"
    uuid snapshot_id FK
  }
  snapshot {
    uuid id PK
    text source
    timestamptz fetched_at
    text s3_key
    text sha256
    int rows_loaded
    text status
  }
```

Rules carried over from the problem domain:

- **Name matching.** Registers and boundary data spell some towns differently
  and some names repeat across counties. Joins use a normalised name *and* the
  county; a settlement served by several plants takes the worst status.
- **Capacity wording.** "No spare capacity" means a Confirmation of
  Feasibility from Uisce Éireann and possibly an upgrade: time and cost, not
  a refusal. The UI uses the register's words and never colours or phrases it
  as a block.
- **Residential is not housing.** Many residential applications create no
  dwelling (extensions, retention). The brief says "residential planning
  applications" unless it filters to new dwellings. In the data, `residential`
  is true only when an application states dwellings: a unit count above zero
  or a one-off house.
- **County comes from the planning authority.** The 31 authorities map onto the
  26 counties (the four Dublin councils to Dublin, city and county councils
  together). An authority the table does not know rejects the run.
- **Planning activity counts applications, not projects.** One scheme can be
  filed, withdrawn and filed again. The dashboard says "applications" and shows
  whether it counts all applications or residential ones only.
- **Decision classes.** Councils word decisions differently ("Conditional",
  "Grant Permission", "Refuse"). The pipeline maps each raw decision to a class
  through one tested table; anything unmapped is counted as "other" and raised as
  a validation warning, never guessed. The raw wording is kept. A blank decision
  falls back to the application's status (withdrawn, invalid), otherwise it is
  pending. Against the data from 2020, the table recognises all but 0.1% of rows.
- **Planning activity is not construction.** A grant is not a start on site.
  Construction starts need commencement notices, which are a separate source
  with their own licence check (open question below).
- **Protected sites are near the town, not the site.** The brief lists SACs,
  SPAs and NHAs whose boundary lies within 5 km of the settlement boundary, with
  the shortest distance between the two boundaries, banded "touches or overlaps
  the town", "within 1 km" and "within 5 km". It describes the town's
  surroundings; it is not an Appropriate Assessment screening and says so.
  Proposed NHAs are not in v1. Boundaries are fetched simplified to about 10 m,
  which cuts the SPA download from 47 MB to 4 MB and is far finer than the bands.
  A site published as several features is merged into one.
- **Coordinates** are stored in Irish Transverse Mercator (EPSG:2157) and
  reprojected only for display.

## 6. Pipeline

One pipeline run per source, scheduled nightly on GitHub Actions, each step idempotent and
keyed by a run id.

1. **Fetch** the source and write the untouched file, gzipped, to
   `raw/<source>/<YYYY-MM-DD>/<run_id>.geojson.gz` in the raw store, with the
   SHA-256 of the uncompressed file. Copies older than 7 days are pruned after
   each run, except the newest copy of each source (planning is about 10 MB a
   night compressed, so the 1 GB free Storage holds the window easily).
2. **Validate** before touching the database: expected columns present, no
   applicant name or address fields, row count within ±20% of the last good
   run (configurable per source), geometries valid.
3. **Transform** into the table shapes above.
4. **Load** into staging tables, then swap into the live tables in one
   transaction. A failed run leaves yesterday's data in place.
5. **Record** a `snapshot` row and emit metrics: rows loaded, duration,
   outcome, data age.

A failed run fails the workflow (GitHub emails the owner) and, once monitoring
lands, raises a Grafana Cloud alert. A run can be replayed from any stored raw
file, which makes backfills and bug fixes cheap. What to do when it fails:
[`docs/runbooks/pipeline-failed.md`](runbooks/pipeline-failed.md).

**Sources (v1)**

| Source | What | Licence |
|---|---|---|
| Uisce Éireann wastewater capacity registers | Plant status per settlement | No licence stated; quoted with attribution and edition date |
| National Planning Applications (Department of Housing, ArcGIS REST) | Applications and decisions | CC BY 4.0 |
| Tailte Éireann settlement boundaries | Settlement polygons | CC BY 4.0, attribution "© Tailte Éireann" |
| NPWS designated areas (ArcGIS REST, the service named on npws.ie) | SAC, SPA and NHA boundaries, one source each | CC BY 4.0 |

## 7. API

Versioned under `/v1`, JSON only, one error shape `{"error": {"code", "message"}}`.

| Method and path | Purpose |
|---|---|
| `GET /health` | Process is up (liveness) |
| `GET /ready` | Database reachable and data younger than 48 h (readiness) |
| `GET /metrics` | Prometheus metrics: request counts and latency by route, data age |
| `GET /v1/settlements?q=` | Search settlements |
| `GET /v1/stats/applications?county=&residential=&from=&to=` | Planning activity: counts by decision class, per county and per month, with the snapshot's capture date. No county means all of Ireland |
| `GET /v1/settlements/{id}/brief?units=&type=` | Assemble the brief: capacity, applications, protected sites, alternatives, each with source and capture date. First slice live: planning precedents (residential applications in the boundary over five years: counts by decision class, the ten most recent, all applications for context); protected sites (SACs, SPAs and NHAs within 5 km of the boundary, nearest first); the other sections are listed as `pending`. `units` and `type` arrive with the capacity section |
| `POST /v1/settlements/{id}/brief/summary` | Optional AI summary over the brief's facts; rate-limited and cached |

Inside the API: routers (HTTP only) → services (brief assembly, rules above)
→ repositories (SQL). The OpenAPI schema is exported in CI and the web client
is generated from it, so the two cannot drift.

## 8. AI summary

- Input is the brief's facts as JSON with ids; output must cite those ids.
  A summary that cites an unknown id or a number not in the facts is
  rejected and the template summary is shown instead.
- Provider-agnostic (any OpenAI-compatible API); Gemini's free tier by
  default.
- Cached by a hash of the facts, so repeat views cost nothing.
- If the quota is exhausted or the call fails, the brief is complete without
  it. The AI is never on the critical path.

## 9. Reliability

| SLI | SLO | Measured by |
|---|---|---|
| Availability | 99.0% of probes succeed, monthly | External uptime probe every 10 minutes (`ops/probe.py`, scheduled GitHub Actions) |
| Latency | p95 under 800 ms for `/v1/…/brief` and `/v1/stats/…`, warm | API metrics |
| Freshness | Data age under 48 h | `/ready` and pipeline metrics |
| Pipeline success | 95% of nightly runs succeed per 30 days | Snapshot log |

**Free-tier trade-off, stated up front.** Render's free service sleeps after
15 minutes idle and takes tens of seconds to wake. The probe runs every 10
minutes, which keeps it awake (one service uses about 730 of the 750 free
hours a month), and each check retries three times, 20 seconds apart, so a cold
start is not counted as an outage. The SLO is 99.0%, not 99.9%. The error
budget and any breach are written up honestly rather than hidden.

**Incidents are GitHub issues.** When a check fails all its attempts, the probe
opens an issue labelled `incident` (one per check: API down, data stale,
dashboard API failing) linking its runbook, and closes it with the outage length
when the check passes again. The issue list is the public incident log. Latency
over a check's budget is reported as "slow" in the run summary, never as down.
**Grafana Cloud, as code.** Its hosted scraper reads `/metrics` every minute
(bearer token). `terraform/stacks/observability` defines the scrape job, a
service dashboard (requests, p95 latency against the SLO, server errors, data
age) and four alerts emailed to the owner: slow responses (p95 of `/v1` over
0.8 s for 10 minutes), server errors (over 5% for 10 minutes, `/ready` excluded
because its 503 means stale data), data stale (over 48 hours) and metrics
missing (nothing for 20 minutes). Each alert links its runbook.

Each alert has a runbook in `docs/runbooks/`: API down, data stale, pipeline
failed; database near its 500 MB limit and Storage near its 1 GB limit come with
the Grafana alerts.

## 10. Security

| Threat | Control |
|---|---|
| Leaked cloud credentials | None exist: CI uses OIDC and short-lived roles |
| CI compromise changing infrastructure | Plan role is read-only; apply needs the approved `production` environment; apply role limited to `dwellwise-*` and to roles under a permissions boundary it cannot change |
| Vulnerable dependencies or images | Dependabot; Trivy on the IaC and on both images (HIGH or CRITICAL with a fix fails the build); an SPDX SBOM attested to every published image |
| Tampered build artefacts | Images pushed to GHCR by digest and signed keyless with cosign (GitHub OIDC, Sigstore). The nightly pipeline runs only the digest it has verified was signed by this repository's `images` workflow on `main`. Render still builds the app from source; moving it to the signed image is the next step |
| Abuse of the AI endpoint | Per-IP and daily limits; cached responses; works without it |
| Secrets in git | gitleaks on full history; push protection on |
| Personal data | Applicant fields excluded at fetch and asserted absent at validation |

## 11. Environments and delivery

- **Pull request:** lint, test, type-check, Terraform plan, security scans, and
  the AWS modules applied to a throwaway Floci emulator.
- **Merge to main:** `.github/workflows/images.yml` builds both images,
  scans them with Trivy, pushes them to GHCR, signs each digest with cosign
  (keyless) and attests its SBOM; on pull requests it builds and scans without
  pushing. Terraform apply (Render, Supabase, GitHub) after approval; Render
  deploys. OpenSSF Scorecard runs weekly and on merge (`scorecard.yml`) and
  publishes its result.
- **Observability:** `.github/workflows/observability.yml` plans the Grafana
  stack on pull requests and applies it on merge. Its state sits in the
  project's Postgres (Terraform's `pg` backend, schema `terraform_observability`),
  so no state service or extra account is needed; tokens are secrets of the
  `observability` environment. The stack's `terraform` service account has the
  **Admin** role: with Editor, Grafana Cloud let it create a folder but refused
  to read it back (`folders:read`), which broke the first apply. Admin is what
  Grafana documents for provisioning; on a one-person stack the wider scope
  (it could also manage users) is an accepted trade-off. A narrower custom role
  is the upgrade path if the stack ever has more users.
- **Nightly:** `.github/workflows/pipeline.yml` builds the same pipeline image
  CI scans and runs it at 03:17 UTC: migrate, every source in order, prune.
  Database and Storage credentials are secrets of the `nightly` environment, so
  no other job can read them; values reach the container through an env file,
  never a command line. It can also be started by hand for one source.
- **Staging and production:** two Supabase projects (the free tier allows
  two); staging receives every merge, production on release.

## 12. Cost

| Service | Use | Monthly |
|---|---|---|
| Render | API container | $0 (free web service) |
| Supabase | Postgres + PostGIS, 500 MB | $0 (free) |
| GitHub Actions schedule, Supabase Storage | Nightly pipeline and raw files (1 GB free) | $0 |
| Grafana Cloud, Sentry, uptime probe | Observability | $0 (free tiers) |
| Gemini API | Optional summaries | $0 (free tier) |
| GitHub Actions | CI/CD on a public repo | $0 |

## 13. Decisions

| Decision | Chosen | Instead of | Because |
|---|---|---|---|
| Brief engine | Deterministic facts + optional AI summary | AI agent choosing tools | Testable, reliable on free quotas, monitorable |
| Cloud account | None: GitHub, Render, Supabase, Grafana Cloud | AWS free plan | No account that can bill; AWS is kept for another project. The AWS Terraform will be tested against the Floci emulator instead |
| Pipeline runtime | Scheduled GitHub Actions | Lambda + EventBridge Scheduler | No cloud account needed; free on a public repo; runs replayable from the raw store |
| Terraform state for Grafana | Postgres `pg` backend in Supabase | HCP Terraform, S3 | Free, already there, has locking; no extra account. Kept in its own schema |
| App hosting | Render free | AWS App Runner or ECS | No free tier on those; Render is free with Docker |
| Database | Supabase (Postgres + PostGIS) | Amazon RDS | Free without expiry; PostGIS included |
| State locking (AWS modules) | S3-native lock file | DynamoDB table | One less resource; Terraform 1.10+ |
| Encryption at rest | SSE-S3 | Customer-managed KMS key | A KMS key costs ~$1/month; recorded as a reasoned scanner suppression |

## 14. Milestones

1. **Foundation** (done): keyless CI, scanning, AWS modules (written, not deployed;
   to be tested against the Floci emulator in CI).
2. **Delivery** (done): plan on pull request, apply on approval, drift check.
   Moves to the Render, Supabase and GitHub providers.
3. **Data:** pipeline core with counties and settlements (done); nightly run on
   GitHub Actions with raw copies in Supabase Storage; capacity registers,
   planning applications and protected sites; tests on fixtures; replay from the
   raw store.
4. **API** (first slice done): `/v1` endpoints, health, readiness, metrics; tests against a
   PostGIS container in CI.
5. **Web** (first slice done): hierarchical web app on the `/v1` API. The
   Ireland page becomes the national planning dashboard (F9) once planning
   applications load; each county page shows its own figures.
6. **Operate:** uptime probe with incidents as issues and runbooks (done);
   Grafana Cloud dashboards (service health and the same planning counts as
   metrics) and alerts, defined in Terraform; error tracking.
7. **Supply chain:** SBOM, signed images, OpenSSF Scorecard.
8. **Kubernetes:** Helm chart deployed to a throwaway cluster in CI.

## 15. Open questions

- Which register editions to keep: latest only, or history to show status
  changes over time?
- Whether staging needs its own Storage bucket or can share one with a prefix.
- How far back to load planning applications. v1 loads applications received
  from 1 January 2020 (about 264,000 of 513,000), to stay well inside the 500 MB
  database; widen it once the table's size is measured.
- Whether commencement notices (Building Control Management System) can be
  used, under what licence, to show construction starts beside planning
  decisions. Not in v1 until checked.
