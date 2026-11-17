# Runbook: nightly pipeline failed

**Signal:** the `nightly pipeline` workflow fails (GitHub emails the owner), or
`/ready` reports a source older than 48 hours.

**What users see:** nothing breaks. A failed run never touches the live tables,
so the site keeps serving the last good data; only its capture date ages.

## Find out which step failed

Open the failed run in the Actions tab. The summary table lists each source with
its status (`loaded`, `rejected`, `failed`) and detail.

| Step failed | Likely cause | What to do |
|---|---|---|
| Write the container environment | A secret or variable is missing | Add it under Settings → Environments → nightly |
| Apply the schema | Database unreachable or password changed | Check Supabase is up; update the `DATABASE_URL` secret |
| Run the sources, status `rejected` | Validation refused the data (row count swing, personal-data field, unknown authority) | Read the detail. If the source really changed, update the source definition in a pull request. Never loosen a check to make a run pass |
| Run the sources, status `failed` | Fetch or load error | Re-run the workflow once. If it fails again, download the raw copy from Supabase Storage and replay it locally |
| Prune | Storage credentials or permissions | Raw copies pile up; not urgent. Fix the access key |

## Re-run one source

Actions → nightly pipeline → Run workflow, with `sources` set to, for example,
`planning`. Counties load before settlements, and settlements before planning.

## Replay a raw copy locally

Every run's raw file is in the Storage bucket under
`raw/<source>/<YYYY-MM-DD>/<run_id>.geojson.gz`, with its SHA-256 (of the
uncompressed file) in `dw.snapshot`.
