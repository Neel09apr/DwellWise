# DwellWise: the one context file

Read this first, every session. It holds **why** the project exists, **what is in
and out of scope**, the **rules**, and **where things stand**. The design lives in
[`docs/DESIGN.md`](docs/DESIGN.md); the README is the public front door. Do not
start other status or handoff files: they drift. Update the Status section in the
same pull request as the work it describes.

## Why this exists

DwellWise is a portfolio project built and operated like a production service.
It exists to demonstrate, in public, the skills behind **Cloud, DevSecOps,
Support/Monitoring, Cloud-SRE and Platform Engineering** roles:

- infrastructure as code (Terraform: Render, Supabase and GitHub for real; the
  AWS modules kept and tested against an emulator in CI),
- secure, keyless delivery (OIDC, least privilege, scanning, signed artefacts),
- reliable data pipelines,
- observability with service-level objectives, alerts and runbooks,
- containers and, later, Kubernetes.

The product gives that work a real purpose: an evidence-backed **pre-planning
brief** for small housing schemes in Ireland, built from public data. Every piece
of work should make one of those skills more visible or the product more useful.
If it does neither, it is drift.

## Scope

**In (v1)**, as specified in `docs/DESIGN.md`:

- Settlement search and a brief per settlement: wastewater capacity, planning
  precedents, protected sites nearby, nearby alternatives with capacity.
- An optional AI summary written only over computed facts.
- A national planning dashboard on the Ireland page: applications granted,
  refused and pending, per county and month, refreshed nightly (F9).
- The platform around it: Terraform, CI/CD, scanning, monitoring, SLOs.

**Out**, unless this file is changed first:

- Planning advice or a likelihood of permission.
- Flood data (OPW licence is CC-BY-NC-ND).
- Applicant names or addresses, at any stage.
- User accounts (drafts stay in the browser for v1).
- Paid services of any kind.

## Rules

1. **$0 per month.** Free tiers only: Render, Supabase, Grafana Cloud, Sentry,
   GitHub Actions. No paid service and no cloud account that can bill.
2. **No AWS account.** The owner keeps AWS for another project (decided
   10 November 2026). The nightly pipeline runs on scheduled GitHub Actions, raw
   files go to Supabase Storage (S3-compatible), secrets are GitHub Actions
   secrets, metrics and alerts go to Grafana Cloud. Terraform applies the real
   Render, Supabase and GitHub settings through CI after approval; no click-ops.
   The AWS Terraform in `terraform/` is kept and will be tested against the
   Floci emulator in CI: call it "tested against an emulator", never "deployed".
3. **Original code only.** Everything here is written for this repository. Do not
   copy code from elsewhere; reuse knowledge of the problem, not files.
4. **Design first.** Changes of scope or architecture update `docs/DESIGN.md` in
   the same pull request, or before it.
5. **One milestone per pull request.** Each PR passes CI, says what was verified
   and what was not, and is merged only on the owner's go-ahead.
6. **Facts from code, never from the model.** The AI summary may only rephrase
   facts it is given, citing them.
7. **Domain wording.** "No spare capacity" means a Confirmation of Feasibility and
   possibly an upgrade: time and cost, not a refusal. Use the register's words.
   Settlement evidence describes the town, never the user's site. "Residential"
   is not "housing".
10. **Design.** Minimal and hierarchical: Ireland > county > settlement > brief, with
    breadcrumbs and numbered sections. One serif, one sans, mono for metadata;
    survey blue is the only accent; green, amber and red are for capacity status only.
8. **Security defaults.** No long-lived cloud keys. Least privilege. Non-root
   containers. Every scanner suppression is scoped and gives its reason.
9. **Tests that can fail.** A new check is mutation-tested before it is trusted.

## Layout

```
app/api        FastAPI: /health /ready /metrics, /v1 counties, settlements, briefs, stats; serves the web app
app/web        React + TypeScript; minimal, hierarchical: Ireland > county > settlement > brief
pipeline/      nightly ingestion (GitHub Actions): fetch, gzipped raw copy, validate, atomic load, prune
terraform/     stacks/observability (Grafana Cloud) and stacks/github (repository settings), applied by CI, state in Postgres; AWS bootstrap, stacks/data, modules (not deployed)
docs/          DESIGN.md; runbooks and decision records as they are written
.github/       CI: lint, tests (PostGIS), Trivy, gitleaks, plan/apply; images (GHCR, cosign, SBOM); Scorecard; nightly pipeline; uptime probe
ops/           uptime probe (stdlib Python), run every 10 minutes by .github/workflows/uptime.yml
```

## Status (21 November 2026)

| Milestone (DESIGN.md §14) | State |
|---|---|
| 1. Foundation: keyless CI, scanning, AWS modules (not deployed) | Merged |
| 2. Delivery: plan on PR, apply on approval, weekly drift check | Merged |
| 3. Data: pipeline core, counties and settlements | Merged (part 1) |
| 3. Data: planning applications (from 2020) | Merged (PR #18); loaded 17 Nov |
| 4–5. API and web app | Merged (PR #6); live at https://dwellwise.onrender.com since 17 Nov |
| 5. National planning dashboard (F9) | Merged (PR #19); live 17 Nov |
| 3. Data: nightly pipeline on GitHub Actions | Merged (PR #20); running nightly since 17 Nov |
| 5. Brief: planning precedents section (F4) | Merged (PR #24); live 21 Nov |
| 3/5. Data and brief: protected sites (SAC, SPA, NHA) and section 03 (F5) | Merged (PR #31); loaded and live 21 Nov |
| 6. Operate: uptime probe, incidents as issues, runbooks | Merged (PR #21); probing every 10 minutes |
| 6. Operate: Grafana Cloud dashboards and alerts (Terraform) | Merged (PR #22); applied 21 Nov; all four alerts verified, alert email delivered |
| 7. Supply chain: SBOM, signed images, Scorecard | Merged (PR #32); images signed, nightly verifies before running (21 Nov) |
| 2. Delivery: GitHub settings as Terraform (ruleset on main, Dependabot alerts) | Merged (PR #33); applied 21 Nov |
| 5. Brief: wastewater section 01 as a link to the county register (F3) | Merged (PR #34); live 21 Nov |
| 1. Foundation: AWS Terraform applied to the Floci emulator in CI | In review |
| 8. Kubernetes: Helm chart on a throwaway cluster | Not started |


## Next

1. Brief sections fill in as each data source lands (planning precedents first); the UI keeps its hierarchy (see `app/web/src/styles.css`).
2. Wastewater capacity: the registers may not be republished (DESIGN.md §6), so
   section 01 links to them and section 04 waits. Revisit only if the licence changes.
3. Terraform for Render and Supabase settings, applied by CI (GitHub is done).
4. Kubernetes: Helm chart on a throwaway cluster in CI.

## Verify a change

```bash
cd pipeline && ruff check . && ruff format --check . && pytest -q && cd ..
cd app/api && ruff check . && ruff format --check . && pytest -q && python -m dwellwise_api.export_openapi && cd ../..
cd app/web && npm run gen:api && npm run typecheck && npm test && npm run build && cd ../..
terraform fmt -check -recursive terraform
git status --short   # openapi.json and schema.d.ts must be unchanged
```

Database tests need `DATABASE_URL` pointing at PostGIS; they run in CI.
