from datetime import date

from dwellwise_pipeline.raw_store import LocalStore, S3Store, expired, prune

TODAY = date(2026, 11, 20)


def key(source: str, day: str, run: str = "r") -> str:
    return f"raw/{source}/{day}/{run}.geojson.gz"


def test_copies_older_than_the_window_go():
    keys = [key("planning", "2026-11-01"), key("planning", "2026-11-14"), key("planning", "2026-11-19")]
    assert expired(keys, keep_days=7, today=TODAY) == [key("planning", "2026-11-01")]


def test_the_newest_copy_of_each_source_is_kept_however_old():
    keys = [key("counties", "2026-10-01"), key("counties", "2026-10-02"), key("planning", "2026-11-19")]
    assert expired(keys, keep_days=7, today=TODAY) == [key("counties", "2026-10-01")]


def test_keys_that_do_not_look_like_raw_copies_are_never_touched():
    assert expired(["raw/notes.txt", "other/2020-01-01/x"], keep_days=0, today=TODAY) == []


def test_prune_deletes_from_the_store(tmp_path):
    store = LocalStore(tmp_path)
    for k in (key("planning", "2026-11-01"), key("planning", "2026-11-19")):
        store.put(k, b"x")
    assert prune(store, keep_days=7, today=TODAY) == [key("planning", "2026-11-01")]
    assert store.keys("raw/") == [key("planning", "2026-11-19")]


class FakeS3:
    def __init__(self, keys):
        self.objects = set(keys)

    def get_paginator(self, _name):
        objects = self.objects

        class Pages:
            def paginate(self, Bucket, Prefix):  # noqa: N803 - boto3's names
                yield {"Contents": [{"Key": k} for k in sorted(objects) if k.startswith(Prefix)]}

        return Pages()

    def delete_object(self, Bucket, Key):  # noqa: N803
        self.objects.remove(Key)


def test_the_s3_store_lists_and_deletes_by_key():
    s3 = FakeS3([key("planning", "2026-11-01"), key("planning", "2026-11-19")])
    prune(S3Store("snapshots", client=s3), keep_days=7, today=TODAY)
    assert s3.objects == {key("planning", "2026-11-19")}


def test_a_copy_exactly_keep_days_old_is_kept():
    keys = [key("planning", "2026-11-13"), key("planning", "2026-11-19")]
    assert expired(keys, keep_days=7, today=TODAY) == []
