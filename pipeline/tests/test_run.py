import contextlib
import gzip
import hashlib
from dataclasses import replace
from datetime import UTC, datetime

import pytest

from dwellwise_pipeline.load import LoadError
from dwellwise_pipeline.raw_store import LocalStore
from dwellwise_pipeline.run import run_source
from dwellwise_pipeline.sources import SOURCES
from dwellwise_pipeline.validate import ValidationError


def test_dry_run_stores_the_exact_bytes_it_validated(tmp_path, counties):
    counties["features"] *= 13  # 26 rows, the minimum for counties
    store = LocalStore(tmp_path)
    when = datetime(2026, 11, 8, 3, 0, tzinfo=UTC)

    result = run_source(SOURCES["counties"], store, fetch=lambda *a: counties, now=when)

    assert result.status == "validated" and result.rows == 26
    key = f"raw/counties/2026-11-08/{result.run_id}.geojson.gz"
    assert hashlib.sha256(gzip.decompress(store.get(key))).hexdigest() == result.sha256


def test_dry_run_still_rejects_bad_data_but_keeps_the_raw_copy(tmp_path, counties):
    with pytest.raises(ValidationError):
        run_source(SOURCES["counties"], LocalStore(tmp_path), fetch=lambda *a: counties)
    assert list(tmp_path.rglob("*.geojson.gz")), "the raw file is kept for diagnosis"


def test_a_run_reads_through_the_sources_own_fetch(tmp_path, counties):
    counties["features"] *= 13
    source = replace(SOURCES["counties"], fetch=lambda: counties)
    assert run_source(source, LocalStore(tmp_path)).rows == len(counties["features"])


def test_a_run_registers_its_source_before_fetching_so_a_failed_first_run_is_known(tmp_path):
    executed = []

    class RecordingConn:
        def execute(self, sql, params=None):
            executed.append((sql.split()[0:3], params))

    def failing_fetch():
        raise RuntimeError("the source is down")

    with pytest.raises(RuntimeError):
        run_source(SOURCES["prices"], LocalStore(tmp_path), RecordingConn(), fetch=failing_fetch)
    (statement, params), *_ = executed
    assert statement == ["insert", "into", "dw.source"]
    assert params == ("prices", SOURCES["prices"].attribution, list(SOURCES).index("prices"))


def test_a_load_stops_before_its_loader_when_a_source_it_needs_is_empty(tmp_path, settlements):
    class Cursor:
        sql: list[str] = []

        def __enter__(self):
            return self

        def __exit__(self, *_exc):
            return False

        def execute(self, sql, params=None):
            self.sql.append(sql)

        def fetchone(self):
            return (False,)  # dw.county is empty

    class Conn:
        cursor_ = Cursor()
        statuses: list[str] = []

        def execute(self, sql, params=None):
            if sql.startswith("insert into dw.snapshot"):
                self.statuses.append(params[6])
            return self

        def fetchone(self):
            return None  # no earlier loaded run

        def transaction(self):
            return contextlib.nullcontext()

        def cursor(self):
            return self.cursor_

    conn = Conn()
    with pytest.raises(LoadError, match="load counties before settlements"):
        run_source(
            replace(SOURCES["settlements"], min_rows=1), LocalStore(tmp_path), conn, fetch=lambda: settlements
        )
    assert conn.cursor_.sql == ["select exists (select from dw.county)"]  # the loader never ran
    assert conn.statuses[-1] == "failed"
