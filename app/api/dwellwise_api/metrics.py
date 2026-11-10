"""Prometheus metrics. Routes are labelled by template, never by raw path."""

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram

REGISTRY = CollectorRegistry()

REQUESTS = Counter(
    "dwellwise_http_requests_total", "HTTP requests", ["method", "route", "status"], registry=REGISTRY
)
LATENCY = Histogram(
    "dwellwise_http_request_duration_seconds",
    "HTTP request duration",
    ["method", "route"],
    buckets=(0.025, 0.05, 0.1, 0.25, 0.5, 0.8, 1, 2.5, 5),  # 0.8 s is the latency SLO
    registry=REGISTRY,
)
DATA_AGE = Gauge(
    "dwellwise_data_age_hours", "Hours since each source last loaded", ["source"], registry=REGISTRY
)


def observe(method: str, route: str, status: int, seconds: float) -> None:
    REQUESTS.labels(method, route, str(status)).inc()
    LATENCY.labels(method, route).observe(seconds)
