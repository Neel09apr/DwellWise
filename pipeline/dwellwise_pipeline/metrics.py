"""One JSON line per source run on stdout, for the workflow summary and, later, Grafana."""

import json


def emit(source: str, succeeded: bool, rows: int) -> None:
    line = {"metric": "pipeline_run", "source": source, "succeeded": succeeded, "rows": rows}
    print(json.dumps(line), flush=True)  # noqa: T201
