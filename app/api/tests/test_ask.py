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


def sample(name: str, labels: dict | None = None) -> float:
    from dwellwise_api.metrics import REGISTRY

    return REGISTRY.get_sample_value(name, labels or {}) or 0.0


def test_outcomes_tokens_and_todays_use_are_measured():
    good = CASES[0]
    service = AskService(scripted(good["turns"]), Gate())
    before = sample("dwellwise_ai_questions_total", {"outcome": "answered"})
    cached_before = sample("dwellwise_ai_questions_total", {"outcome": "cached"})
    asyncio.run(service.ask(good["question"], None, "a", recorded(good["tool_results"])))
    asyncio.run(service.ask(good["question"], None, "a", recorded(good["tool_results"])))
    assert sample("dwellwise_ai_questions_total", {"outcome": "answered"}) == before + 1
    assert sample("dwellwise_ai_questions_total", {"outcome": "cached"}) == cached_before + 1
    assert sample("dwellwise_ai_today", {"kind": "questions"}) == 1
    assert sample("dwellwise_ai_today", {"kind": "tokens"}) == 30  # three scripted model calls of 10 tokens
    assert sample("dwellwise_ai_daily_limit", {"kind": "questions"}) == 800

    refused = next(c for c in CASES if c["name"] == "a rounded price is refused")
    before = sample("dwellwise_ai_questions_total", {"outcome": "refused"})
    refusing = AskService(scripted(refused["turns"]))
    asyncio.run(refusing.ask(refused["question"], None, "b", recorded(refused["tool_results"])))
    assert sample("dwellwise_ai_questions_total", {"outcome": "refused"}) == before + 1


def test_limited_and_unavailable_questions_are_counted():
    limited = sample("dwellwise_ai_questions_total", {"outcome": "limited"})
    with pytest.raises(Limited):
        asyncio.run(AskService(scripted([]), Gate(per_ip_hour=0)).ask("q?", None, "a", recorded({})))
    assert sample("dwellwise_ai_questions_total", {"outcome": "limited"}) == limited + 1

    def down(_messages, _tools):
        raise AiUnavailable("down")

    unavailable = sample("dwellwise_ai_questions_total", {"outcome": "unavailable"})
    with pytest.raises(AiUnavailable):
        asyncio.run(AskService(down).ask("q?", None, "a", recorded({})))
    assert sample("dwellwise_ai_questions_total", {"outcome": "unavailable"}) == unavailable + 1


def test_model_calls_are_counted_per_provider():
    ok = sample("dwellwise_ai_model_calls_total", {"provider": "p1", "outcome": "ok"})
    failed = sample("dwellwise_ai_model_calls_total", {"provider": "p0", "outcome": "failed"})

    def post(provider, _body):
        if provider.name == "p0":
            raise urllib.error.HTTPError("u", 503, "down", {}, None)
        return {"choices": [{"message": {"content": "ok"}}], "usage": {"total_tokens": 5}}

    ChatClient([Provider("p0", "https://a", "m", "k"), Provider("p1", "https://b", "m", "k")], post)([], [])
    assert sample("dwellwise_ai_model_calls_total", {"provider": "p1", "outcome": "ok"}) == ok + 1
    assert sample("dwellwise_ai_model_calls_total", {"provider": "p0", "outcome": "failed"}) == failed + 1
    assert sample("dwellwise_ai_tokens_total", {"provider": "p1"}) >= 5


def test_the_models_tool_calls_are_not_counted_as_visitors():
    app = create_app(Settings())
    args = {"homes": 8, "floor_area_m2": 110, "build_cost_per_m2": 2800, "contribution": 117,
            "contribution_basis": "per_m2", "fees_pct": 10, "contingency_pct": 5, "finance_rate_pct": 8,
            "finance_months": 18}  # fmt: skip
    visitor = {"method": "GET", "route": "/v1/costs", "status": "200"}
    before = sample("dwellwise_http_requests_total", visitor)
    tool = sample("dwellwise_ai_tool_calls_total", {"tool": "cost_estimate", "status": "200"})
    asyncio.run(AppTools(app)("cost_estimate", args))
    assert sample("dwellwise_http_requests_total", visitor) == before
    assert sample("dwellwise_ai_tool_calls_total", {"tool": "cost_estimate", "status": "200"}) == tool + 1
    with TestClient(app) as c:
        c.get("/v1/costs", params=args)
    assert sample("dwellwise_http_requests_total", visitor) == before + 1


def test_the_status_says_whether_the_assistant_is_on():
    with TestClient(create_app(Settings())) as c:
        assert c.get("/v1/assistant").json() == {"enabled": False}
    with TestClient(create_app(Settings(ai_api_key="k"))) as c:
        assert c.get("/v1/assistant").json() == {"enabled": True}


def test_todays_tokens_start_again_at_midnight_utc():
    now = [1_800_000_000.0]
    gate = Gate(clock=lambda: now[0])
    gate.admit("a")
    gate.spend(150_000)
    gate.report()
    assert sample("dwellwise_ai_today", {"kind": "tokens"}) == 150_000
    now[0] += 86_400
    gate.admit("a")
    gate.report()
    assert sample("dwellwise_ai_today", {"kind": "tokens"}) == 0
    assert sample("dwellwise_ai_today", {"kind": "questions"}) == 1


def test_a_tool_call_the_provider_rejects_becomes_the_refusal_not_an_outage():
    import io

    def post(_provider, _body):
        body = io.BytesIO(
            b'{"error":{"code":"tool_use_failed","message":"run_sql was not in request.tools"}}'
        )
        raise urllib.error.HTTPError("u", 400, "Bad Request", {}, body)

    client = ChatClient([Provider("groq", "https://g", "m", "k")], post)
    assert client([], [])["message"] == {"content": ""}
    result = asyncio.run(answer("What is being built in Athy?", "1", client, recorded({})))
    assert (result["grounded"], result["answer"]) == (False, REFUSAL)

    def other_400(_provider, _body):
        raise urllib.error.HTTPError("u", 400, "Bad Request", {}, io.BytesIO(b'{"error":{"code":"invalid"}}'))

    with pytest.raises(AiUnavailable, match="HTTP 400"):
        ChatClient([Provider("groq", "https://g", "m", "k")], other_400)([], [])


def test_a_refusal_logs_the_numbers_that_failed_and_never_the_question(caplog):
    import logging

    refused = next(c for c in CASES if c["name"] == "a rounded price is refused")
    with caplog.at_level(logging.INFO, logger="dwellwise.api.ask"):
        result = asyncio.run(
            AskService(scripted(refused["turns"])).ask(
                refused["question"], None, "203.0.113.9", recorded(refused["tool_results"])
            )
        )
    assert result["ungrounded"] == ["420"]
    (line,) = [r.getMessage() for r in caplog.records if "assistant_refused" in r.getMessage()]
    assert json.loads(line) == {"event": "assistant_refused", "ungrounded": ["420"], "tools": ["sale_prices"]}
    assert refused["question"] not in line and "203.0.113.9" not in line
