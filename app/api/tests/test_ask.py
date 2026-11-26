"""The assistant without a model: scripted transcripts replayed through the real loop, tools and checks.

The transcripts in ai_eval/cases.json are written by hand, not recorded from a
model: they fix how the loop, the tool allow-list and the grounding check must
behave, so a change that lets an unchecked number through fails the build.
"""

import asyncio
import json
import urllib.error
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import dwellwise_api.routers.ask as ask_route
from dwellwise_api.ai_client import AiUnavailable, ChatClient, Provider
from dwellwise_api.ai_tools import TOOLS, AppTools, request_for
from dwellwise_api.ask import REFUSAL, AskService, Gate, Limited, answer
from dwellwise_api.config import Settings
from dwellwise_api.main import create_app

CASES = json.loads((Path(__file__).parent / "ai_eval" / "cases.json").read_text(encoding="utf-8"))


def scripted(turns):
    script = list(turns)

    def chat(_messages, _tools):
        return {"message": script.pop(0), "provider": "script", "tokens": 10}

    chat.script = script
    return chat


def recorded(results):
    ran = []

    async def tools(name, arguments):
        if name not in TOOLS:  # the real runner refuses these before any request; so does this stand-in
            return json.dumps({"error": f"no tool is called {name}"})
        ran.append(name)
        return results[name]

    tools.ran = ran
    return tools


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_the_eval_set(case):
    tools = recorded(case["tool_results"])
    result = asyncio.run(answer(case["question"], case["settlement"], scripted(case["turns"]), tools))
    assert result["grounded"] is (case["expect"] == "grounded")
    if case["expect"] == "rejected":
        assert result["answer"] == REFUSAL
    else:
        assert result["answer"] == case["turns"][-1]["content"]
    if "expect_tools" in case:
        assert result["tools"] == case["expect_tools"]
    for name in case.get("expect_not_run", []):
        assert name not in tools.ran


def test_tool_calls_become_only_allow_listed_routes():
    assert request_for("settlement_brief", {"code": "../../health"}) == (
        "/v1/settlements/..%2F..%2Fhealth/brief",
        {},
    )
    assert request_for("sale_prices", {"settlement": "11016", "sql": "drop", "county": {"x": 1}}) == (
        "/v1/prices", {"settlement": "11016"},
    )  # fmt: skip
    assert request_for("application_stats", {"residential": True})[1] == {"residential": "true"}
    with pytest.raises(KeyError):
        request_for("run_sql", {})


def test_tools_run_through_the_app_itself_with_its_validation():
    app = create_app(Settings())  # no database: the cost estimate needs none
    tools = AppTools(app)
    args = {"homes": 8, "floor_area_m2": 110, "build_cost_per_m2": 2800, "contribution": 117,
            "contribution_basis": "per_m2", "fees_pct": 10, "contingency_pct": 5, "finance_rate_pct": 8,
            "finance_months": 18}  # fmt: skip
    ok = json.loads(asyncio.run(tools("cost_estimate", args)))
    assert ok["status"] == 200 and ok["body"]["total"] == 3_112_754
    bad = json.loads(asyncio.run(tools("cost_estimate", {**args, "homes": 0})))
    assert bad["status"] == 422
    assert "no tool" in json.loads(asyncio.run(tools("run_sql", {})))["error"]


def test_the_gate_limits_each_visitor_and_the_day_and_caches_for_a_day():
    now = [1_800_000_000.0]
    gate = Gate(per_ip_hour=2, daily_cap=3, clock=lambda: now[0])
    gate.admit("a")
    gate.admit("a")
    with pytest.raises(Limited, match="2 questions an hour"):
        gate.admit("a")
    gate.admit("b")
    with pytest.raises(Limited, match="as many questions as it can today"):
        gate.admit("c")
    now[0] += 86_400  # a new day, and more than an hour later for "a"
    gate.admit("a")
    gate.remember(("q", ""), {"answer": "x"})
    assert gate.cached(("q", "")) == {"answer": "x"}
    now[0] += 86_401
    assert gate.cached(("q", "")) is None


def test_a_failing_provider_hands_over_to_the_next_and_none_means_unavailable():
    calls = []

    def post(provider, _body):
        calls.append(provider.name)
        if provider.name == "groq":
            raise urllib.error.HTTPError("u", 429, "busy", {}, None)
        return {"choices": [{"message": {"content": "ok"}}], "usage": {"total_tokens": 7}}

    client = ChatClient(
        [Provider("groq", "https://g", "m", "k"), Provider("fallback", "https://f", "m", "k")], post
    )
    assert client([], []) == {"message": {"content": "ok"}, "provider": "fallback", "tokens": 7}
    assert calls == ["groq", "fallback"]
    with pytest.raises(AiUnavailable):
        ChatClient([Provider("groq", "https://g", "m", "k")], post)([], [])


def test_without_a_key_the_assistant_is_off_and_says_so():
    with TestClient(create_app(Settings())) as c:
        response = c.post("/v1/ask", json={"question": "What do homes sell for in Navan?"})
    assert response.status_code == 503
    assert "switched off" in response.json()["error"]["message"]


def test_the_kill_switch_wins_over_a_key():
    assert Settings(ai_api_key="k", ai_enabled=False).ai_providers() == []
    assert Settings.from_env({"AI_API_KEY": "k", "AI_ENABLED": "false"}).ai_providers() == []
    assert [p.name for p in Settings.from_env({"AI_API_KEY": "k"}).ai_providers()] == ["groq"]


def test_the_route_checks_answers_caches_good_ones_and_limits_visitors(monkeypatch):
    case = CASES[0]
    chat = scripted(case["turns"])

    async def tools(name, _arguments):
        return case["tool_results"][name]

    monkeypatch.setattr(ask_route, "AppTools", lambda _app: tools)
    app = create_app(Settings())
    with TestClient(app) as c:
        app.state.ai = AskService(chat, Gate(per_ip_hour=1, daily_cap=10))
        first = c.post("/v1/ask", json={"question": "What do homes sell for in Navan?"})
        again = c.post("/v1/ask", json={"question": "  what do HOMES sell for in navan? "})
        other = c.post("/v1/ask", json={"question": "Another question here"})
        too_long = c.post("/v1/ask", json={"question": "x" * 501})
    assert first.status_code == 200
    assert (first.json()["grounded"], first.json()["cached"]) == (True, False)
    assert first.json()["tools"] == ["search_settlements", "sale_prices"]
    assert (
        again.json()["cached"] is True and chat.script == []
    )  # the cache answered; the script was used once
    assert other.status_code == 429
    assert too_long.status_code == 422


def test_a_refused_answer_is_not_cached_so_the_next_ask_tries_again():
    rejected = next(c for c in CASES if c["name"] == "a rounded price is refused")
    chat = scripted(rejected["turns"] * 2)
    service = AskService(chat, Gate())
    tools = recorded(rejected["tool_results"])
    first = asyncio.run(service.ask(rejected["question"], rejected["settlement"], "a", tools))
    second = asyncio.run(service.ask(rejected["question"], rejected["settlement"], "a", tools))
    assert first["grounded"] is False and second["cached"] is False
    assert chat.script == []  # the model was asked twice


def test_the_key_never_shows_and_a_malformed_reply_counts_as_a_failure():
    provider = Provider("groq", "https://g", "m", "sk-secret")
    assert "sk-secret" not in repr(provider)
    with pytest.raises(AiUnavailable, match="malformed reply"):
        ChatClient([provider], lambda _p, _b: {"choices": []})([], [])
