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

- infrastructure as code (Terraform on AWS),
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

1. **$0 per month.** Free tiers only: Render, Supabase, AWS free plan, Grafana
   Cloud, Sentry, GitHub Actions. A $1 AWS budget alarm guards it. Avoid anything
   that silently upgrades the AWS free plan (Organizations, Control Tower,
   IAM Identity Center).
2. **AWS for anything that needs a big cloud.** Infrastructure goes through
   Terraform in `terraform/`, applied by CI after approval. No click-ops.
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
8. **Security defaults.** No long-lived cloud keys. Least privilege. Non-root
   containers. Every scanner suppression is scoped and gives its reason.
9. **Tests that can fail.** A new check is mutation-tested before it is trusted.

## Layout

```
app/api        FastAPI: /health /ready /metrics, /v1 settlements; serves the web app
app/web        React + TypeScript (working UI; visual design to come from Claude Design)
pipeline/      nightly ingestion: fetch, raw copy to S3, validate, atomic load
terraform/     bootstrap (state, OIDC roles, budget), stacks/, modules/
docs/          DESIGN.md; runbooks and decision records as they are written
.github/       CI: lint, tests (PostGIS), image builds, Trivy, gitleaks, plan/apply
```

## Status (8 November 2026)

| Milestone (DESIGN.md §14) | State |
|---|---|
| 1. Foundation: AWS baseline, keyless CI, scanning | Merged |
| 2. Delivery: plan on PR, apply on approval, weekly drift check | Merged |
| 3. Data: pipeline core, counties and settlements | Merged (part 1) |
| 4–5. API and web app | In progress: API, minimal web UI, container, Render blueprint |
| 6. Operate: uptime, dashboards, errors, SLOs, runbooks | Not started |
| 7. Supply chain: SBOM, signed images, Scorecard | Not started |
| 8. Kubernetes: Helm chart on a throwaway cluster | Not started |

**Blocked on the owner:** an AWS account (free plan, IAM admin user with MFA) to
run the bootstrap; nothing in AWS exists yet.

## Next

1. Finish milestone 4–5: run the app locally against Supabase, merge, deploy to Render.
2. Visual design of the web app with Claude Design, then implement it in `app/web`.
3. Pipeline sources: wastewater capacity registers, planning applications,
   protected sites; then the brief endpoint.
4. AWS bootstrap, then the Lambda and scheduler for the nightly pipeline.

## Verify a change

```bash
cd pipeline && ruff check . && ruff format --check . && pytest -q && cd ..
cd app/api && ruff check . && ruff format --check . && pytest -q && python -m dwellwise_api.export_openapi && cd ../..
cd app/web && npm run gen:api && npm run typecheck && npm test && npm run build && cd ../..
terraform fmt -check -recursive terraform
git status --short   # openapi.json and schema.d.ts must be unchanged
```

Database tests need `DATABASE_URL` pointing at PostGIS; they run in CI.
