"""Application factory: routes, error shape, observability, security headers, web app."""

from __future__ import annotations

import json
import logging
import mimetypes
import time
import uuid
from contextlib import asynccontextmanager
from http import HTTPStatus

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse
from starlette.exceptions import HTTPException

from . import db, metrics
from .ai_client import ChatClient
from .ask import AskService, Gate
from .config import Settings
from .place import Places, load_from_database
from .routers import ask, costs, counties, health, maps, prices, settlements, stats

log = logging.getLogger("dwellwise.api")

# The map's worker is an ES module (.mjs). Browsers refuse a module worker served
# with any type but JavaScript, and not every platform's MIME table knows .mjs.
mimetypes.add_type("text/javascript", ".mjs")

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": (
        "default-src 'self'; img-src 'self' data: blob: https://tiles.openfreemap.org; "
        "style-src 'self' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; "
        "connect-src 'self' https://tiles.openfreemap.org; worker-src 'self'; "
        "frame-ancestors 'none'; base-uri 'self'"
    ),
}


def _error(status: int, message: str) -> JSONResponse:
    code = HTTPStatus(status).phrase.lower().replace(" ", "_")
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=status)


def init_error_tracking(settings: Settings) -> None:
    """Send unhandled errors to Sentry when a DSN is set. No tracing: Grafana has latency."""
    if not settings.sentry_dsn:
        return
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        release=settings.release,
        environment="production",
        include_local_variables=False,  # frame locals hold request headers and the database URL
        traces_sample_rate=0,
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    init_error_tracking(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.pool = db.open_pool(settings.database_url)
        try:
            yield
        finally:
            db.close_pool(app.state.pool)

    app = FastAPI(title="DwellWise API", version="0.1.0", lifespan=lifespan, redoc_url=None)
    app.state.settings = settings
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.state.pool = None
    app.state.places = Places(load_from_database)
    providers = settings.ai_providers()
    app.state.ai = (
        AskService(
            ChatClient(providers), Gate(per_ip_hour=settings.ai_per_ip_hour, daily_cap=settings.ai_daily_cap)
        )
        if providers
        else None
    )  # None: /v1/ask answers 503 and nothing else changes
    app.include_router(health.router)
    app.include_router(counties.router)
    app.include_router(settlements.router)
    app.include_router(stats.router)
    app.include_router(maps.router)
    app.include_router(prices.router)
    app.include_router(costs.router)
    app.include_router(ask.router)

    @app.exception_handler(HTTPException)
    async def http_error(_request: Request, exc: HTTPException) -> JSONResponse:
        return _error(exc.status_code, str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def invalid_request(_request: Request, exc: RequestValidationError) -> JSONResponse:
        first = exc.errors()[0] if exc.errors() else {}
        where = ".".join(str(p) for p in first.get("loc", ()) if p not in ("query", "path"))
        return _error(422, f"{where}: {first.get('msg', 'invalid value')}" if where else "Invalid request.")

    @app.exception_handler(Exception)
    async def unexpected(_request: Request, exc: Exception) -> JSONResponse:
        # Details go to the logs, and to Sentry through its FastAPI integration; never the response.
        log.exception("unhandled error")
        return _error(500, "Something went wrong on our side.")

    @app.middleware("http")
    async def observe(request: Request, call_next):
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        start = time.perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
        finally:
            elapsed = time.perf_counter() - start
            route = getattr(request.scope.get("route"), "path", "unmatched")
            metrics.observe(request.method, route, status, elapsed)
            log.info(
                json.dumps(
                    {
                        "request_id": request_id,
                        "method": request.method,
                        "route": route,
                        "status": status,
                        "duration_ms": round(elapsed * 1000, 1),
                    }
                )
            )
        response.headers["X-Request-ID"] = request_id
        response.headers.update(SECURITY_HEADERS)
        return response

    dist = settings.web_dist
    if dist and (dist / "index.html").is_file():
        root = dist.resolve()

        @app.api_route("/{path:path}", methods=["GET", "HEAD"], include_in_schema=False)
        async def web_app(path: str):
            if path.startswith("v1/"):
                raise HTTPException(404, "No such API route.")
            candidate = (root / path).resolve()
            if path and candidate.is_file() and candidate.is_relative_to(root):
                immutable = path.startswith("assets/")  # hashed file names
                cache = "public, max-age=31536000, immutable" if immutable else "no-cache"
                return FileResponse(candidate, headers={"Cache-Control": cache})
            # Client-side routes (for example /settlements/123) all serve the app.
            return FileResponse(root / "index.html", headers={"Cache-Control": "no-cache"})

    return app


logging.basicConfig(level=logging.INFO, format="%(message)s")
app = create_app()
