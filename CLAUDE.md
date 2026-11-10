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
app/api        FastAPI: /health /ready /metrics, /v1 counties and settlements; serves the web app
app/web        React + TypeScript; minimal, hierarchical: Ireland > county > settlement > brief
pipeline/      nightly ingestion: fetch, raw copy to object storage, validate, atomic load
terraform/     AWS bootstrap, stacks/, modules/ (not deployed); Render/Supabase/GitHub to come
docs/          DESIGN.md; runbooks and decision records as they are written
.github/       CI: lint, tests (PostGIS), image builds, Trivy, gitleaks, plan/apply
```

## Status (10 November 2026)

| Milestone (DESIGN.md §14) | State |
|---|---|
| 1. Foundation: keyless CI, scanning, AWS modules (not deployed) | Merged |
| 2. Delivery: plan on PR, apply on approval, weekly drift check | Merged |
| 3. Data: pipeline core, counties and settlements | Merged (part 1) |
| 4–5. API and web app | Merged (PR #6); Render deploy next |
| 6. Operate: uptime, dashboards, errors, SLOs, runbooks | Not started |
| 7. Supply chain: SBOM, signed images, Scorecard | Not started |
| 8. Kubernetes: Helm chart on a throwaway cluster | Not started |


## Next

1. Deploy to Render (the owner sets `DATABASE_URL` in the Render dashboard).
2. Brief sections fill in as each data source lands; the UI keeps its hierarchy (see `app/web/src/styles.css`).
3. Pipeline sources: wastewater capacity registers, planning applications,
   protected sites; then the brief endpoint.
4. Nightly pipeline on a GitHub Actions schedule, raw copies to Supabase Storage.
5. CI job that applies the AWS Terraform to the Floci emulator.
6. Terraform for Render, Supabase and GitHub settings, applied by CI.

## Verify a change

```bash
cd pipeline && ruff check . && ruff format --check . && pytest -q && cd ..
cd app/api && ruff check . && ruff format --check . && pytest -q && python -m dwellwise_api.export_openapi && cd ../..
cd app/web && npm run gen:api && npm run typecheck && npm test && npm run build && cd ../..
terraform fmt -check -recursive terraform
git status --short   # openapi.json and schema.d.ts must be unchanged
```

Database tests need `DATABASE_URL` pointing at PostGIS; they run in CI.
