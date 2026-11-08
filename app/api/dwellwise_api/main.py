"""Application factory: routes, error shape, observability, security headers, web app."""

from __future__ import annotations

import json
import logging
import time
import uuid
from contextlib import asynccontextmanager
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from starlette.exceptions import HTTPException

from . import db, metrics
from .config import Settings
from .routers import health, settlements

log = logging.getLogger("dwellwise.api")

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": (
        "default-src 'self'; img-src 'self' data:; "
        "style-src 'self' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; "
        "connect-src 'self'; frame-ancestors 'none'; base-uri 'self'"
    ),
}


def _error(status: int, message: str) -> JSONResponse:
    code = HTTPStatus(status).phrase.lower().replace(" ", "_")
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=status)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.pool = db.open_pool(settings.database_url)
        try:
            yield
        finally:
            db.close_pool(app.state.pool)

    app = FastAPI(title="DwellWise API", version="0.1.0", lifespan=lifespan, redoc_url=None)
    app.state.settings = settings
    app.state.pool = None
    app.include_router(health.router)
    app.include_router(settlements.router)

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
        log.exception("unhandled error")  # details stay in the logs, never in the response
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

        @app.get("/{path:path}", include_in_schema=False)
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
