"""Immutable copies of every fetched file, so any run can be replayed."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path


def raw_key(source: str, fetched_at: datetime, run_id: str) -> str:
    return f"raw/{source}/{fetched_at:%Y-%m-%d}/{run_id}.geojson"


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


class S3Store:
    """The snapshots bucket in AWS."""

    def __init__(self, bucket: str, client=None) -> None:
        if client is None:
            import boto3  # only needed in AWS; keeps local tests light

            client = boto3.client("s3")
        self.bucket = bucket
        self.client = client

    def put(self, key: str, data: bytes) -> str:
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType="application/geo+json")
        return f"s3://{self.bucket}/{key}"

    def get(self, key: str) -> bytes:
        return self.client.get_object(Bucket=self.bucket, Key=key)["Body"].read()
