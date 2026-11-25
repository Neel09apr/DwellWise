"""Liveness, readiness and metrics."""

from __future__ import annotations

import hmac

from fastapi import APIRouter, HTTPException, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from psycopg import Error as DatabaseError
from psycopg_pool import PoolTimeout

from .. import repositories as repo
from ..metrics import DATA_AGE, REGISTRY
from ..schemas import Health, Ready

router = APIRouter(tags=["health"])

# Sources the app cannot work without. Each must have loaded within FRESHNESS_HOURS.
REQUIRED_SOURCES = ("counties", "settlements", "planning", "sac", "spa", "nha", "commencements", "prices")


@router.get("/health", response_model=Health)
def health() -> Health:
    """The process is up. Used by the platform to restart a dead container."""
    return Health(status="ok")


@router.head("/health", include_in_schema=False)
def health_head() -> Response:
    """Uptime monitors often send HEAD; answer it like GET, without a body."""
    return Response(status_code=200)


@router.get("/ready", response_model=Ready, responses={503: {"model": Ready}})
def ready(request: Request, response: Response) -> Ready:
    """The database answers and every required source is fresh."""
    pool = request.app.state.pool
    if pool is None:
        response.status_code = 503
        return Ready(status="unavailable", checks={"database": "not configured"})
    try:
        with pool.connection(timeout=3) as conn:
            loaded = repo.loaded_sources(conn)
    except (PoolTimeout, DatabaseError):
        response.status_code = 503
        return Ready(status="unavailable", checks={"database": "unreachable"})

    limit = request.app.state.settings.freshness_hours
    checks = {"database": "ok"}
    stale = False
    for source in REQUIRED_SOURCES:
        if source not in loaded:
            checks[f"data:{source}"] = "never loaded"
            stale = True
            continue
        age = float(loaded[source]["age_hours"])
        DATA_AGE.labels(source).set(age)
        checks[f"data:{source}"] = f"{age:.1f} h old"
        stale = stale or age > limit
    if stale:
        response.status_code = 503
        return Ready(status="stale", checks=checks)
    return Ready(status="ready", checks=checks)


@router.get("/metrics", include_in_schema=False)
def metrics(request: Request) -> Response:
    token = request.app.state.settings.metrics_token
    if token and not hmac.compare_digest(request.headers.get("authorization", ""), f"Bearer {token}"):
        raise HTTPException(401, "A bearer token is required.")
    refresh_data_age(request.app.state.pool)
    return Response(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)


def refresh_data_age(pool) -> None:
    """Set data age from the snapshot log on every scrape.

    Without this the gauge only moves when something calls /ready, so the
    "Data stale" alert would go blind if the uptime probe stopped. A database
    problem never fails the scrape; "Metrics missing" and /ready cover outages.
    """
    if pool is None:
        return
    try:
        with pool.connection(timeout=3) as conn:
            for source, row in repo.loaded_sources(conn).items():
                DATA_AGE.labels(source).set(float(row["age_hours"]))
    except (PoolTimeout, DatabaseError):
        pass
