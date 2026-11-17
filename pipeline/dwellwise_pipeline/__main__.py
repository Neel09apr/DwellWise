"""Local runner.

python -m dwellwise_pipeline migrate
python -m dwellwise_pipeline run [counties settlements planning] [--dry-run]
python -m dwellwise_pipeline prune [--keep-days 7] [--raw-dir raw]
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict
from datetime import date
from pathlib import Path

from .dburl import normalise
from .load import migrate
from .raw_store import LocalStore, S3Store, prune
from .run import run_source
from .sources import SOURCES


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="dwellwise_pipeline")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("migrate", help="apply the SQL schema to DATABASE_URL")
    run = sub.add_parser("run", help="run sources in order")
    # No default here: argparse would check a list default against choices as one value.
    run.add_argument("sources", nargs="*", choices=list(SOURCES), help="default: all, in order")
    run.add_argument(
        "--dry-run", action="store_true", help="fetch, store raw and validate; skip the database"
    )
    run.add_argument("--raw-dir", type=Path, default=Path("raw"), help="where raw files go without S3")
    clean = sub.add_parser(
        "prune", help="delete raw copies older than --keep-days (keeps each source's newest)"
    )
    clean.add_argument("--keep-days", type=int, default=7)
    clean.add_argument("--raw-dir", type=Path, default=Path("raw"), help="where raw files are without S3")
    args = parser.parse_args(argv)
    if args.command == "run" and not args.sources:
        args.sources = list(SOURCES)
    return args


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    bucket = os.environ.get("SNAPSHOT_BUCKET")
    store = S3Store(bucket) if bucket else LocalStore(args.raw_dir) if args.command != "migrate" else None

    if args.command == "prune":
        gone = prune(store, args.keep_days, date.today())
        print(json.dumps({"pruned": len(gone), "keys": gone}))  # noqa: T201
        return

    if args.command == "run" and args.dry_run:
        for name in args.sources:
            print(json.dumps(asdict(run_source(SOURCES[name], store))))  # noqa: T201
        return

    import psycopg

    with psycopg.connect(normalise(os.environ["DATABASE_URL"]), autocommit=True) as conn:
        if args.command == "migrate":
            migrate(conn)
            print("schema up to date")  # noqa: T201
            return
        for name in args.sources:
            print(json.dumps(asdict(run_source(SOURCES[name], store, conn))))  # noqa: T201


if __name__ == "__main__":
    main()
