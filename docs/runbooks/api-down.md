# Runbook: API down

**Signal:** an `Incident: API down` or `Incident: Dashboard API failing` issue,
opened by the uptime probe after three failed attempts about 20 seconds apart.

**What users see:** the site does not load, or the dashboard shows an error.

## Check, in order

1. **Is Render up?** https://status.render.com. If Render has an incident, wait
   and note it on the issue; there is nothing to fix here.
2. **Did a deploy just happen?** Render → dwellwise → Events. A failed deploy
   keeps the previous version running; a bad one that went live can be rolled
   back from the same page (Rollback on the last good deploy).
3. **Logs.** Render → dwellwise → Logs. Every request is one JSON line with a
   `request_id`; errors are logged with their stack trace, never shown to users.
4. **Database.** If `/health` passes but data endpoints return 503 "database is
   not configured" or "unreachable", check `DATABASE_URL` in Render's Environment
   and Supabase's status page. A changed password must be updated in Render, the
   `nightly` environment and `app/api/.env`.

## After

The probe closes the issue itself with the outage length. Add a short note on
the issue: cause, what fixed it, and anything to change so it does not recur.
