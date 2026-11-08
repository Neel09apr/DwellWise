"""A small connection pool, opened with the app and closed with it."""

from __future__ import annotations

from collections.abc import Iterator

from fastapi import HTTPException, Request
from psycopg_pool import ConnectionPool, PoolTimeout


def open_pool(url: str | None) -> ConnectionPool | None:
    if not url:
        return None
    # min_size=0: the free-tier database is not held open while the app sleeps.
    pool = ConnectionPool(url, min_size=0, max_size=4, timeout=5, open=False, kwargs={"autocommit": True})
    pool.open(wait=False)
    return pool


def close_pool(pool: ConnectionPool | None) -> None:
    if pool is not None:
        pool.close()


def get_conn(request: Request) -> Iterator:
    pool: ConnectionPool | None = request.app.state.pool
    if pool is None:
        raise HTTPException(503, "The database is not configured.")
    try:
        conn = pool.getconn()
    except PoolTimeout as exc:
        raise HTTPException(503, "The database is unavailable. Try again shortly.") from exc
    try:
        yield conn
    finally:
        pool.putconn(conn)
