"""The model's tools: DwellWise's own public API, and nothing else.

Each tool is a GET to one allow-listed /v1 route, made in-process through the
app's ASGI interface. Arguments go through the same validation and place
resolution as a visitor's request, so the model can do nothing a visitor
cannot: no SQL, no web, no other route.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.parse import quote, urlencode

from .metrics import AI_TOOL_CALLS

INTERNAL_HOST = "dwellwise.internal"  # the middleware leaves these requests out of visitor metrics
MAX_RESULT_CHARS = 6000  # ponytail: Groq's free tier allows ~8,000 tokens a minute; trim big briefs to fit


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    path: str  # may hold {code}
    params: dict[str, dict]  # JSON schema per argument
    required: tuple[str, ...] = ()

    def spec(self) -> dict:
        schema = {"type": "object", "properties": self.params, "required": list(self.required)}
        return {
            "type": "function",
            "function": {"name": self.name, "description": self.description, "parameters": schema},
        }


COUNTY = {"type": "string", "description": "County name, e.g. Meath"}
SETTLEMENT = {"type": "string", "description": "CSO settlement code from search_settlements, e.g. 11016"}
MONTH = {"type": "string", "description": "YYYY-MM"}
NUMBER = {"type": "number"}

TOOLS = {
    t.name: t
    for t in (
        Tool(
            "search_settlements",
            "Find towns by name; returns their CSO codes and counties.",
            "/v1/settlements",
            {"q": {"type": "string"}, "county": COUNTY},
            ("q",),
        ),
        Tool(
            "settlement_brief",
            "A town's pre-planning brief: planning precedents and protected sites nearby.",
            "/v1/settlements/{code}/brief",
            {"code": SETTLEMENT},
            ("code",),
        ),
        Tool(
            "application_stats",
            "Planning applications per month by decision, for Ireland or one county.",
            "/v1/stats/applications",
            {"county": COUNTY, "residential": {"type": "boolean"}, "from": MONTH, "to": MONTH},
        ),
        Tool(
            "commencement_stats",
            "Homes whose construction started, per month, for Ireland, a county or a town.",
            "/v1/stats/commencements",
            {"county": COUNTY, "settlement": SETTLEMENT, "from": MONTH, "to": MONTH},
        ),
        Tool(
            "sale_prices",
            "CSO median sale prices for the area around a town, a county or Ireland.",
            "/v1/prices",
            {"county": COUNTY, "settlement": SETTLEMENT},
        ),
        Tool(
            "shortlist",
            "A county's top five towns for a scheme, side by side: planning precedents, homes started, "
            "protected sites within 1 km and the area's median sale price, sorted by one column.",
            "/v1/shortlist",
            {
                "county": COUNTY,
                "sort": {"type": "string", "enum": ["started", "granted", "protected", "price"]},
            },
            ("county",),
        ),
        Tool(
            "cost_estimate",
            "A scheme's cost from figures the user gave; never invent a figure.",
            "/v1/costs",
            {
                "homes": NUMBER,
                "floor_area_m2": NUMBER,
                "build_cost_per_m2": NUMBER,
                "contribution": NUMBER,
                "contribution_basis": {"type": "string", "enum": ["per_m2", "per_home"]},
                "fees_pct": NUMBER,
                "contingency_pct": NUMBER,
                "finance_rate_pct": NUMBER,
                "finance_months": NUMBER,
                "land": NUMBER,
            },
        ),
    )
}

SPECS = [t.spec() for t in TOOLS.values()]


def request_for(name: str, arguments: dict) -> tuple[str, dict]:
    """The route and query a tool call becomes. Unknown tools and undeclared arguments never get through."""
    tool = TOOLS.get(name)
    if tool is None:
        raise KeyError(f"no tool is called {name}")
    args = {
        k: v for k, v in arguments.items() if k in tool.params and isinstance(v, str | int | float | bool)
    }
    path = tool.path
    if "{code}" in path:
        path = path.replace("{code}", quote(str(args.pop("code", "")), safe=""))
    query = {k: (str(v).lower() if isinstance(v, bool) else v) for k, v in args.items()}
    return path, query


async def asgi_get(app, path: str, query: dict) -> tuple[int, object]:
    """One GET through the app itself, no network: the same middleware, validation and errors."""
    scope = {
        "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1", "method": "GET", "scheme": "http",
        "path": path, "raw_path": path.encode(), "root_path": "", "query_string": urlencode(query).encode(),
        "headers": [(b"host", INTERNAL_HOST.encode()), (b"accept", b"application/json")],
        "client": ("127.0.0.1", 0), "server": (INTERNAL_HOST, 80),
    }  # fmt: skip
    status, body = 500, bytearray()

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        nonlocal status
        if message["type"] == "http.response.start":
            status = message["status"]
        elif message["type"] == "http.response.body":
            body.extend(message.get("body", b""))

    await app(scope, receive, send)
    return status, json.loads(body) if body else None


class AppTools:
    """Runs tool calls against the app; returns what the model sees as text."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, name: str, arguments: dict) -> str:
        try:
            path, query = request_for(name, arguments)
        except KeyError as exc:
            AI_TOOL_CALLS.labels("not_allowed", "refused").inc()
            return json.dumps({"error": str(exc)})
        status, body = await asgi_get(self.app, path, query)
        AI_TOOL_CALLS.labels(name, str(status)).inc()
        text = json.dumps({"status": status, "body": body}, ensure_ascii=False, separators=(",", ":"))
        return text[:MAX_RESULT_CHARS]
