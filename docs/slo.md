# Service-level objectives and error budget

What "working" means for DwellWise, how it is measured, and what happens when
it is not met. The numbers live in the Grafana dashboard "DwellWise service"
(the SLO panels at the bottom); this page is the policy.

## Objectives

| SLI | Objective | Window | Measured by |
|---|---|---|---|
| Availability | 99.0% of `/health` checks pass | rolling 14 days | Grafana Synthetic Monitoring: `/health` every 2 minutes from Frankfurt and London, must answer 200 with `"status": "ok"` over TLS within 10 s |
| Freshness | 99.0% of `/ready` checks pass | rolling 14 days | The same probes, `/ready` every 10 minutes: database reachable and every source under 48 hours old |
| Latency | p95 under 800 ms on `/v1` routes | 10 minutes | API metrics scraped every minute (alert "Slow responses") |
| Pipeline | 95% of nightly runs succeed | 30 days | The snapshot log and the workflow history |

**Why 14 days, not a month.** Grafana Cloud's free tier keeps metrics for 14
days, so a longer window cannot be computed from them. 14 days is still long
enough to smooth out a single bad night.

**Why 99.0%.** The app runs on Render's free plan: one instance, restarted on
every deploy, with no zero-downtime guarantee. 99.0% allows about 3.4 hours of
failed checks in 14 days, which that platform can meet; 99.9% (20 minutes)
would be a promise the platform cannot keep.

**Why synthetic checks, not GitHub's cron.** The first probe ran on a scheduled
GitHub Actions workflow. In its first five hours GitHub fired none of its
scheduled runs (the nightly pipeline's schedule ran about eight hours late the
same day). An SLO needs samples at a steady rate, so measurement moved to
Grafana's probes. The GitHub probe stays as a backup that opens and closes
incident issues when it does run. See
[the write-up](incidents/2026-11-21-uptime-probe-never-scheduled.md).

## Error budget

The budget is the 1% of checks that may fail: about 3.4 hours of a 14-day
window. The dashboard shows how much is left; below zero, the SLO is breached.

**Burn-rate alerts** (emailed, each linking its runbook). Burn rate is the
current error rate divided by 1%; a burn rate of 1 spends the budget exactly
over 14 days.

| Alert | Fires when | Means |
|---|---|---|
| Error budget burning fast | burn rate over 14.4 for both the last hour and the last 10 minutes | about 4% of the budget an hour; all of it within a day |
| Error budget burning slowly | burn rate over 6 for both the last 6 hours and the last 30 minutes | the budget would be gone in under 2.5 days |

Two windows per alert: the long one shows the problem is big enough to matter,
the short one that it is still happening, so an outage that has ended does not
keep alerting.

## Policy

While budget remains, changes ship as normal: one milestone per pull request,
merged when CI is green.

When the budget is exhausted (the SLO is breached for the current window):

1. Feature work stops. Only changes that restore reliability, or that cannot
   wait (security fixes), are merged until the 14-day availability is back
   above 99.0%.
2. Every outage that spent more than 25% of the budget gets a write-up in
   [`docs/incidents/`](incidents/) within a week, using the template there.
3. The write-up's actions are done before feature work resumes, or explicitly
   deferred in the write-up with a reason.

A breach caused by the free platform itself (a Render incident, a forced
restart) is still counted. It is written up, and if it recurs, the answer is a
reasoned change to the objective in this file, not a quiet exclusion.

## Reading the numbers

- Dashboard: Grafana, folder "DwellWise", dashboard "DwellWise service", SLO panels.
- Incidents: GitHub issues labelled `incident` (opened by the probe) and the
  write-ups in [`docs/incidents/`](incidents/).
- Runbooks: [`docs/runbooks/`](runbooks/).
