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


# The assistant (/v1/ask). Its model calls are slow by nature, so it has its own metrics and is
# left out of the API's latency and error SLOs; its tool calls are not visitor requests.
AI_QUESTIONS = Counter(
    "dwellwise_ai_questions_total",
    "Questions to the assistant, by outcome: answered, refused, cached, limited, unavailable",
    ["outcome"],
    registry=REGISTRY,
)
AI_MODEL_CALLS = Counter(
    "dwellwise_ai_model_calls_total", "Calls to a model provider", ["provider", "outcome"], registry=REGISTRY
)
AI_TOKENS = Counter("dwellwise_ai_tokens_total", "Tokens used, by provider", ["provider"], registry=REGISTRY)
AI_TOOL_CALLS = Counter(
    "dwellwise_ai_tool_calls_total",
    "The model's calls to DwellWise's own API",
    ["tool", "status"],
    registry=REGISTRY,
)
AI_SECONDS = Histogram(
    "dwellwise_ai_answer_seconds",
    "Time to answer a question that reached the model",
    buckets=(1, 2, 5, 10, 20, 40),
    registry=REGISTRY,
)
AI_TODAY = Gauge(
    "dwellwise_ai_today", "Use so far today (UTC), by kind: questions, tokens", ["kind"], registry=REGISTRY
)
AI_DAILY_LIMIT = Gauge(
    "dwellwise_ai_daily_limit", "Daily limit, by kind: the question cap, the provider's tokens", ["kind"],
    registry=REGISTRY,
)  # fmt: skip


def observe(method: str, route: str, status: int, seconds: float) -> None:
    REQUESTS.labels(method, route, str(status)).inc()
    LATENCY.labels(method, route).observe(seconds)
