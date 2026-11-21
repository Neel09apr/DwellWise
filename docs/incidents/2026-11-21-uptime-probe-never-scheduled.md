# Uptime probe never ran on its schedule

| | |
|---|---|
| Date | 2026-11-21 |
| Duration | at least 5 hours unmonitored (14:01 to after 19:00 UTC) |
| User impact | None known. Nothing was checking the site, so an outage would have gone unnoticed |
| Error budget spent | Not measurable: there were no samples |
| Detected by | A person, while building the SLO report: the workflow had one run in five hours |

## Summary

The uptime probe was a GitHub Actions workflow scheduled every 10 minutes. After
it was merged, GitHub ran it once by hand and then never on its schedule. The
README said the site was "probed every 10 minutes"; it was not probed at all.
Nothing alerted, because the thing that would have alerted was the probe.

## Timeline (UTC)

- 14:00  PR #21 merges the probe workflow (`*/10 * * * *`).
- 14:01  A manual run passes. This was taken as proof that the probe worked.
- 14:01–19:00  No scheduled run is created. The same day, the nightly pipeline's
  03:17 schedule had started at 10:56, nearly eight hours late.
- ~19:10  Building an SLO report from probe history finds one run in total.
  The GitHub API confirms: workflow active, one run, `workflow_dispatch`.
- ~19:30  Decision: measure availability with Grafana Synthetic Monitoring;
  keep the GitHub probe only as a backup that files incident issues.

## What went wrong

- **GitHub's scheduler is best effort.** Scheduled runs can start late or not at
  all when GitHub is busy, and new schedules can take time to register. That is
  fine for a nightly job with a 48-hour freshness margin; it cannot carry an
  availability objective that needs a steady sample rate.
- **The monitor was not monitored.** A manual run showed the probe *could*
  work, not that it *was* working. Nothing checked that results kept arriving.
- **Documentation stated an intention as a fact.** "Probed every 10 minutes"
  was written when the workflow merged, before a single scheduled run.

## What went well

- The gap was found by trying to use the data, before anyone relied on an SLO
  number built on it.
- The incident flow (issues opened and closed by the probe) was already built
  and tested by the manual run, so it still serves as a backup.

## Actions

| Action | Status |
|---|---|
| Measure availability and freshness with Grafana Synthetic Monitoring, as Terraform: `/health` every 2 min and `/ready` every 10 min from two locations | Done in this PR |
| Alert when synthetic results stop arriving ("Synthetic checks missing"): a heartbeat for the monitor itself | Done in this PR |
| Correct the README and DESIGN.md: the GitHub probe is a backup, not the measurement | Done in this PR |
| Before calling a scheduled job "running", check that a scheduled run actually happened | Practice; noted in CLAUDE.md |
