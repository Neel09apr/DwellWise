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
    """The database answers and every registered source loaded within FRESHNESS_HOURS.

    The pipeline registers its sources in dw.source; an empty registry is not ready.
    """
    pool = request.app.state.pool
    if pool is None:
        response.status_code = 503
        return Ready(status="unavailable", checks={"database": "not configured"})
    try:
        with pool.connection(timeout=3) as conn:
            sources = repo.registered_sources(conn)
    except (PoolTimeout, DatabaseError):
        response.status_code = 503
        return Ready(status="unavailable", checks={"database": "unreachable"})

    limit = request.app.state.settings.freshness_hours
    checks = {"database": "ok"}
    if not sources:
        response.status_code = 503
        return Ready(status="stale", checks={**checks, "sources": "none registered"})
    stale = False
    for source in sources:
        name = source["name"]
        if source["age_hours"] is None:
            checks[f"data:{name}"] = "never loaded"
            stale = True
            continue
        age = float(source["age_hours"])
        DATA_AGE.labels(name).set(age)
        checks[f"data:{name}"] = f"{age:.1f} h old"
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
    """Set data age for every registered source on every scrape.

    Without this the gauge only moves when something calls /ready, so the
    "Data stale" alert would go blind if the uptime probe stopped. A database
    problem never fails the scrape; "Metrics missing" and /ready cover outages.
    """
    if pool is None:
        return
    try:
        with pool.connection(timeout=3) as conn:
            for source in repo.registered_sources(conn):
                if source["age_hours"] is not None:
                    DATA_AGE.labels(source["name"]).set(float(source["age_hours"]))
    except (PoolTimeout, DatabaseError):
        pass
