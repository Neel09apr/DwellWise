"""The live evaluation's own logic, without the network: what counts as a pass."""

import asyncio
import json

from tests.ai_eval import live


def script(turns):
    queue = list(turns)
    return lambda _m, _t: {"message": queue.pop(0), "provider": "script", "tokens": 1}


def test_a_case_passes_only_when_grounded_and_the_named_tools_were_called():
    case = next(c for c in live.CASES if c["name"] == "a price quoted exactly is shown")
    assert live.run_case(case, script(case["turns"]))[0] is True
    skipped_tool = [case["turns"][2]]  # answers without calling sale_prices: its figures are not grounded
    assert live.run_case(case, script(skipped_tool))[0] is False


def test_a_tool_without_a_recording_answers_not_recorded():
    text = asyncio.run(live.recorded({})("settlement_brief", {}))
    assert json.loads(text)["status"] == 404


def test_without_a_key_the_live_run_skips_rather_than_fails(monkeypatch, capsys):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    assert live.main() == 0
    assert "skipping" in capsys.readouterr().out


def test_seven_cases_are_asked_live():
    assert sum("live_must_call" in c for c in live.CASES) == 7


def test_a_grounded_answer_that_skipped_the_tool_still_fails():
    case = next(c for c in live.CASES if c["name"] == "a total the data gives is shown with its months")
    no_tools = [{"role": "assistant", "content": "I do not have that."}]  # no numbers: grounded
    passed, result = live.run_case(case, script(no_tools))
    assert result["grounded"] is True and passed is False


def test_a_list_in_must_call_accepts_any_one_of_its_tools():
    case = next(c for c in live.CASES if c["name"] == "an unknown place is reported, not invented")
    search = {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {"id": "s", "type": "function", "function": {"name": "search_settlements", "arguments": "{}"}}
        ],
    }
    reply = {"role": "assistant", "content": "There is no county called Ballykilty in the data."}
    assert live.run_case(case, script([search, reply]))[0] is True
    assert live.run_case(case, script([reply]))[0] is False  # no check at all
