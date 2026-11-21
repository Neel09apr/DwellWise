# Runbook: data stale

**Signal:** an `Incident: Data stale` issue: `/ready` returned 503 because a
source has not loaded within 48 hours (or the database is unreachable).

**What users see:** the site works and shows the last good data; capture dates
on the dashboard get older.

## Check, in order

1. **Read the issue's detail.** It holds the `/ready` body, for example
   `"data:planning": "52.0 h old"`, so it names the stale source.
2. **Did the nightly pipeline run?** Actions → nightly pipeline. If recent runs
   failed, follow [pipeline-failed.md](pipeline-failed.md).
3. **Did it not run at all?** GitHub pauses scheduled workflows in a public repo
   after 60 days without commits; re-enable it from the Actions tab and start a
   run by hand.
4. **Database unreachable?** If the body says `"database": "unreachable"`, it is
   an outage, not staleness: follow [api-down.md](api-down.md).

The issue closes itself on the first probe after a successful load.
