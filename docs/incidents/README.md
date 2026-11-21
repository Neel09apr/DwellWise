# Incident write-ups

Blameless write-ups of things that went wrong: outages, near misses, and
changes that failed. The point is what the system and the process allowed, and
what changes so it cannot happen the same way again. When one is required, see
the policy in [`../slo.md`](../slo.md); anything else worth learning from gets
one too.

| Date | Incident | User impact |
|---|---|---|
| 2026-11-21 | [Uptime probe never ran on its schedule](2026-11-21-uptime-probe-never-scheduled.md) | None known; the site was unmonitored for about five hours |
| 2026-11-21 | [SSL enforcement stopped Terraform saving its state](2026-11-21-ssl-enforcement-broke-terraform-state.md) | None; infrastructure changes blocked for seven minutes |

## Template

Copy into `YYYY-MM-DD-short-name.md`.

```markdown
# <What happened, in one line>

| | |
|---|---|
| Date | YYYY-MM-DD |
| Duration | from first impact to recovery |
| User impact | who noticed what, or "none" |
| Error budget spent | minutes, and % of the 14-day budget |
| Detected by | alert / probe / a person, and how long after it started |

## Summary
Two or three sentences a non-engineer can follow.

## Timeline (UTC)
- HH:MM  what happened, what was seen, what was done

## What went wrong
The causes: technical, and in the process. No names; what allowed it.

## What went well

## Actions
| Action | Status |
|---|---|
| ... | done in #PR / open: issue / deferred: why |
```
