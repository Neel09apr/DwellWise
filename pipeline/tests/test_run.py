import gzip
import hashlib
from datetime import UTC, datetime

import pytest

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


def test_the_source_filter_reaches_the_fetch(tmp_path, counties):
    seen = []
    counties["features"] *= 13

    def fetch(*args):
        seen.append(args)
        return counties

    run_source(SOURCES["counties"], LocalStore(tmp_path), fetch=fetch)
    assert seen[0][3] == "1=1"
    seen.clear()
    with pytest.raises(ValidationError):  # the counties fixture is not planning data
        run_source(SOURCES["planning"], LocalStore(tmp_path), fetch=fetch)
    assert seen[0][3] == "ReceivedDate >= DATE '2020-01-01'"


def test_a_run_registers_its_source_before_fetching_so_a_failed_first_run_is_known(tmp_path):
    executed = []

    class RecordingConn:
        def execute(self, sql, params=None):
            executed.append((sql.split()[0:3], params))

    def failing_fetch(*_args):
        raise RuntimeError("the source is down")

    with pytest.raises(RuntimeError):
        run_source(SOURCES["prices"], LocalStore(tmp_path), RecordingConn(), fetch=failing_fetch)
    (statement, params), *_ = executed
    assert statement == ["insert", "into", "dw.source"]
    assert params == ("prices", SOURCES["prices"].attribution, list(SOURCES).index("prices"))
