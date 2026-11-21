# Runbook: slow responses

**Signal:** the Grafana alert "Slow responses": p95 latency of `/v1` routes has
been above the 800 ms SLO for 10 minutes. The uptime probe may also mark checks
"slow" in its run summary (it never opens an incident for slowness alone).

**What users see:** the dashboard and search work, but feel sluggish.

## Check, in order

1. **Which route?** Grafana → DwellWise → DwellWise service → "p95 latency, /v1
   routes". One route points at its query; all of them point at the platform.
2. **Did the service just wake up?** A cold start on Render's free plan takes
   tens of seconds and skews the percentile for a few minutes. If the uptime
   probe stopped running (Actions → uptime), the service is sleeping between
   visitors: re-enable the workflow.
3. **Is the database slow?** Supabase → Reports → Database. The stats query uses
   the `(county, received)` index; a missing index after a schema change shows
   up here first.
4. **Did data volume jump?** A much larger planning load (for example a wider
   date window) makes the national stats query slower; check the latest
   `rows_loaded` in `dw.snapshot`.

## After

Note the cause on the alert or in a short incident issue. If the fix is code (a
query or an index), it goes through a pull request like any other change.
