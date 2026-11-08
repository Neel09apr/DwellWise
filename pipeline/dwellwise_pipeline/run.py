"""One source, one run: fetch, store raw, validate, transform, load, record."""

from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime

from . import metrics
from .arcgis import fetch_features
from .load import LOADERS
from .raw_store import raw_key
from .sources.base import Source
from .validate import ValidationError, validate


@dataclass
class RunResult:
    source: str
    run_id: str
    raw_uri: str
    sha256: str
    rows: int
    status: str
    detail: dict = field(default_factory=dict)


def _last_loaded_rows(conn, source: str) -> int | None:
    row = conn.execute(
        "select rows_loaded from dw.snapshot where source = %s and status = 'loaded' "
        "order by fetched_at desc limit 1",
        (source,),
    ).fetchone()
    return row[0] if row else None


def _record(conn, run: RunResult, fetched_at: datetime, detail: str | None) -> None:
    conn.execute(
        "insert into dw.snapshot (id, source, fetched_at, raw_uri, sha256, rows_loaded, status, detail) "
        "values (%s, %s, %s, %s, %s, %s, %s, %s)",
        (run.run_id, run.source, fetched_at, run.raw_uri, run.sha256, run.rows, run.status, detail),
    )


def run_source(
    source: Source,
    store,
    conn=None,
    *,
    fetch: Callable[..., dict] = fetch_features,
    now: datetime | None = None,
) -> RunResult:
    """Run one source. With no connection it stops after validation (a dry run)."""
    fetched_at = now or datetime.now(UTC)
    run_id = str(uuid.uuid4())
    collection = fetch(source.layer_url, list(source.out_fields), source.order_by)

    data = json.dumps(collection, separators=(",", ":")).encode("utf-8")
    run = RunResult(
        source=source.name,
        run_id=run_id,
        raw_uri=store.put(raw_key(source.name, fetched_at, run_id), data),
        sha256=hashlib.sha256(data).hexdigest(),
        rows=len(collection["features"]),
        status="validated",
    )

    if conn is None:
        validate(source, collection, previous_rows=None)
        return run

    try:
        validate(source, collection, previous_rows=_last_loaded_rows(conn, source.name))
    except ValidationError as exc:
        run.status = "rejected"
        _record(conn, run, fetched_at, str(exc))
        metrics.emit(source.name, succeeded=False, rows=0)
        raise

    rows = source.transform(collection)
    run.rows = len(rows)
    try:
        with conn.transaction():
            run.status = "loaded"
            _record(conn, run, fetched_at, None)
            with conn.cursor() as cur:
                run.detail = LOADERS[source.table](cur, rows, run_id)
    except Exception as exc:
        run.status = "failed"
        _record(conn, run, fetched_at, f"{type(exc).__name__}: {exc}")
        metrics.emit(source.name, succeeded=False, rows=0)
        raise

    metrics.emit(source.name, succeeded=True, rows=run.rows)
    return run
