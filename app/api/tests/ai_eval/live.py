"""The live evaluation: the real model, the recorded tool results, the same checks.

Run by .github/workflows/ai-eval.yml with the GROQ_API_KEY secret:

    cd app/api && python -m tests.ai_eval.live

Each case marked ``live_must_call`` in cases.json is asked of the real model.
Its tools answer from the case's recorded results (a tool with no recording
answers "not recorded"), so the run checks the model and the prompt, not the
data. A case passes when the answer is grounded and the model called every
tool listed. A failing case is asked once more; the model is not
deterministic even at temperature 0. The key is read from the environment and
never printed.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from pathlib import Path

from dwellwise_api.ai_client import ChatClient, Provider
from dwellwise_api.ask import answer
from dwellwise_api.config import Settings

CASES = json.loads((Path(__file__).parent / "cases.json").read_text(encoding="utf-8"))
PAUSE_SECONDS = 8  # Groq's free tier allows ~8,000 tokens a minute, shared with the live site


def paced(chat):
    def call(messages, tools):
        time.sleep(PAUSE_SECONDS)
        return chat(messages, tools)

    return call


def recorded(results: dict):
    async def tools(name: str, _arguments: dict) -> str:
        return results.get(name, json.dumps({"status": 404, "body": {"error": "not recorded"}}))

    return tools


def run_case(case: dict, chat) -> tuple[bool, dict]:
    tools = recorded(case["tool_results"])
    result = asyncio.run(answer(case["question"], case["settlement"], chat, tools, case.get("history")))
    called = set(result["tools"])
    # Each entry is a tool name, or a list of names any one of which will do.
    needs = [{t} if isinstance(t, str) else set(t) for t in case["live_must_call"]]
    passed = result["grounded"] and all(called & need for need in needs)
    if case.get("live_calls_nothing"):  # a scheme with no county: the model must ask, not search
        passed = result["grounded"] and not called
    return passed, result


def main() -> int:
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        print("GROQ_API_KEY is not set: skipping the live evaluation.")  # noqa: T201
        return 0
    settings = Settings()
    chat = paced(ChatClient([Provider("groq", settings.ai_base_url, settings.ai_model, key)]))
    failures = 0
    for case in (c for c in CASES if "live_must_call" in c):
        passed, result = run_case(case, chat)
        if not passed:
            passed, result = run_case(case, chat)  # once more: the model is not deterministic
        failures += not passed
        mark = "PASS" if passed else "FAIL"
        rejected = len(result.get("rejected", []))
        summary = f"grounded={result['grounded']} tools={result['tools']} rejected={rejected}"
        print(f"{mark}  {case['name']}: {summary}")  # noqa: T201
        if not passed:
            print(f"      answer: {result['answer'][:300]!r}")  # noqa: T201
            print(f"      numbers not in the data: {result.get('ungrounded')}")  # noqa: T201
            print(f"      tool calls rejected: {result.get('rejected')}")  # noqa: T201
    print(f"{failures} failed")  # noqa: T201
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
