"""Local runner.

python -m dwellwise_pipeline migrate
python -m dwellwise_pipeline run counties settlements [--dry-run] [--raw-dir raw]
"""

from __future__ import annotations

import argparse
import os
from dataclasses import asdict
from pathlib import Path

from .load import migrate
from .raw_store import LocalStore, S3Store
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
    args = parser.parse_args(argv)
    if args.command == "run" and not args.sources:
        args.sources = list(SOURCES)
    return args


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    bucket = os.environ.get("SNAPSHOT_BUCKET")
    store = S3Store(bucket) if bucket else LocalStore(args.raw_dir) if args.command == "run" else None

    if args.command == "run" and args.dry_run:
        for name in args.sources:
            print(asdict(run_source(SOURCES[name], store)))  # noqa: T201
        return

    import psycopg

    with psycopg.connect(os.environ["DATABASE_URL"], autocommit=True) as conn:
        if args.command == "migrate":
            migrate(conn)
            print("schema up to date")  # noqa: T201
            return
        for name in args.sources:
            print(asdict(run_source(SOURCES[name], store, conn)))  # noqa: T201


if __name__ == "__main__":
    main()
