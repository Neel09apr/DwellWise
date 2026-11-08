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
    key = f"raw/counties/2026-11-08/{result.run_id}.geojson"
    assert hashlib.sha256(store.get(key)).hexdigest() == result.sha256


def test_dry_run_still_rejects_bad_data_but_keeps_the_raw_copy(tmp_path, counties):
    with pytest.raises(ValidationError):
        run_source(SOURCES["counties"], LocalStore(tmp_path), fetch=lambda *a: counties)
    assert list(tmp_path.rglob("*.geojson")), "the raw file is kept for diagnosis"
