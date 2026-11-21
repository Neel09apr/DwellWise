# SSL enforcement stopped Terraform saving its state

| | |
|---|---|
| Date | 2026-11-21 |
| Duration | 7 minutes (18:21 to 18:28 UTC) |
| User impact | None. The site stayed up and kept serving data throughout |
| Error budget spent | None |
| Detected by | The apply job failing, within a minute of the change |

## Summary

A Terraform change switched on SSL enforcement for the database, so the database
refuses connections that are not encrypted. The change worked, but Terraform
stores its own state in that same database and connected to it *without*
encryption, so it could no longer save its state. A second part of the same
change was refused because the access token lacked a permission. A fix merged
seven minutes later.

## Timeline (UTC)

- 18:21  PR #36 merges. Its apply imports the Supabase settings and starts two
  updates.
- 18:21  SSL enforcement is applied. Disabling sign-ups is refused: 403,
  `missing_permissions: project_admin_write`.
- 18:21  Terraform cannot save state: `no pg_hba.conf entry … no encryption`.
  It writes `errored.tfstate` on the runner, which is discarded with it. No
  state had been saved for this stack before, so nothing is lost or forked.
- 18:22  `/ready` checked: the database is fine for the app. Fresh test
  connections: psycopg's default (`prefer`) and `require` connect over TLS;
  `disable` is refused (`ESSLREQUIRED`). So the app and pipeline are safe;
  only Terraform's state connection is affected, including the Grafana and
  GitHub stacks on their next run.
- 18:28  PR #37 merges: the state connection string gets `sslmode=require`, and
  the stack stops managing sign-ups. The apply re-imports and saves state.
- 18:35  The Grafana and GitHub stacks re-run: no changes, state saved over TLS.

## What went wrong

- **An unverified assumption.** The pull request said every client already
  used TLS. The app and pipeline did; Terraform's `pg` backend did not, because
  it does not try TLS unless the connection string asks for it. Nobody checked
  which connections were encrypted before enforcing encryption.
- **A plan cannot show it.** `terraform plan` reads state before the change, so
  it cannot reveal that the change will lock Terraform itself out.
- **Scoped token, unknown requirement.** The token was given "Auth Config
  read-write", but the auth settings API requires `project_admin_write`. Plans
  only read, so the missing write permission surfaced at apply time.

## What went well

- The failure was loud and immediate, and the state backend's locking and
  error handling meant no state was corrupted or forked.
- Checking each client's connection with every `sslmode` gave a clear picture
  in minutes of who was affected and who was not.
- The fix kept the token narrow: sign-ups went to a one-time dashboard change
  instead of giving CI project-wide admin rights.

## Actions

| Action | Status |
|---|---|
| `ops/dburl.py` adds `sslmode=require` for every Terraform workflow; tests cover it | Done in #37 |
| Supabase stack manages SSL enforcement only; sign-ups switched off in the dashboard, recorded in DESIGN.md | Done in #37 |
| Before enforcing a connection requirement, list who connects and test each client against it (for Postgres: `pg_stat_ssl`, or connect with each `sslmode`) | Practice; noted in CLAUDE.md |
