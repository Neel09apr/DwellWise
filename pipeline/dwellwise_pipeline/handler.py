"""AWS Lambda entry point. Event: {"sources": ["counties", "settlements"]}."""

from __future__ import annotations

import os
from dataclasses import asdict

from .raw_store import S3Store
from .run import run_source
from .sources import SOURCES


def database_url() -> str:
    """DATABASE_URL for local use; in AWS, a SecureString in Parameter Store."""
    if url := os.environ.get("DATABASE_URL"):
        return url
    import boto3

    parameter = boto3.client("ssm").get_parameter(Name=os.environ["DATABASE_URL_PARAM"], WithDecryption=True)
    return parameter["Parameter"]["Value"]


def handler(event: dict, context: object) -> dict:
    import psycopg

    names = event.get("sources") or list(SOURCES)
    unknown = [n for n in names if n not in SOURCES]
    if unknown:
        raise ValueError(f"unknown sources: {unknown}; known: {list(SOURCES)}")

    store = S3Store(os.environ["SNAPSHOT_BUCKET"])
    with psycopg.connect(database_url(), autocommit=True) as conn:
        return {"results": [asdict(run_source(SOURCES[n], store, conn)) for n in names]}
