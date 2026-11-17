"""Immutable, gzipped copies of every fetched file, so any run can be replayed.

Keys carry the fetch date: raw/<source>/<YYYY-MM-DD>/<run_id>.geojson.gz. Pruning
reads that date from the key, not the store's clock, and always keeps the newest
copy of each source so a run can be replayed even after a long outage.
"""

from __future__ import annotations

import os
import re
from datetime import date, datetime, timedelta
from pathlib import Path

KEY = re.compile(r"^raw/(?P<source>[^/]+)/(?P<day>\d{4}-\d{2}-\d{2})/[^/]+$")


def raw_key(source: str, fetched_at: datetime, run_id: str) -> str:
    return f"raw/{source}/{fetched_at:%Y-%m-%d}/{run_id}.geojson.gz"


def expired(keys: list[str], keep_days: int, today: date) -> list[str]:
    """Keys older than keep_days, except the newest copy of each source."""
    cutoff = today - timedelta(days=keep_days)
    dated = [(m["source"], date.fromisoformat(m["day"]), k) for k in keys if (m := KEY.match(k))]
    newest = {}
    for source, day, key in dated:
        newest[source] = max(newest.get(source, (day, key)), (day, key))
    keep = {key for _, key in newest.values()}
    return sorted(key for _, day, key in dated if day < cutoff and key not in keep)


def prune(store, keep_days: int, today: date) -> list[str]:
    gone = expired(store.keys("raw/"), keep_days, today)
    for key in gone:
        store.delete(key)
    return gone


class LocalStore:
    """For local runs and tests."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def put(self, key: str, data: bytes) -> str:
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path.resolve().as_uri()

    def get(self, key: str) -> bytes:
        return (self.root / key).read_bytes()

    def keys(self, prefix: str) -> list[str]:
        return sorted(
            p.relative_to(self.root).as_posix() for p in (self.root / prefix).rglob("*") if p.is_file()
        )

    def delete(self, key: str) -> None:
        (self.root / key).unlink()


class S3Store:
    """Any S3-compatible bucket. In production: Supabase Storage through its S3 API.

    SNAPSHOT_ENDPOINT and SNAPSHOT_REGION point boto3 at it; the access key comes
    from the usual AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY variables.
    """

    def __init__(self, bucket: str, client=None) -> None:
        if client is None:
            import boto3
            from botocore.config import Config

            client = boto3.client(
                "s3",
                endpoint_url=os.environ.get("SNAPSHOT_ENDPOINT") or None,
                region_name=os.environ.get("SNAPSHOT_REGION") or None,
                config=Config(s3={"addressing_style": "path"}),  # Supabase needs path-style URLs
            )
        self.bucket = bucket
        self.client = client

    def put(self, key: str, data: bytes) -> str:
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType="application/gzip")
        return f"s3://{self.bucket}/{key}"

    def get(self, key: str) -> bytes:
        return self.client.get_object(Bucket=self.bucket, Key=key)["Body"].read()

    def keys(self, prefix: str) -> list[str]:
        pages = self.client.get_paginator("list_objects_v2").paginate(Bucket=self.bucket, Prefix=prefix)
        return sorted(o["Key"] for page in pages for o in page.get("Contents", []))

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)
