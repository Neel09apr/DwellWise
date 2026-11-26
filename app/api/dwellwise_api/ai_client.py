"""One thin client for OpenAI-compatible chat APIs: Groq's free tier first, a fallback after it.

Standard library only. A provider that answers 429 or 5xx, cannot be reached,
or sends a malformed reply hands the request to the next one; when none
answers, ``AiUnavailable``. Every call is counted per provider.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field

from .metrics import AI_MODEL_CALLS, AI_TOKENS

TIMEOUT_SECONDS = 30


class AiUnavailable(RuntimeError):
    """No configured provider could answer."""


@dataclass(frozen=True)
class Provider:
    name: str
    base_url: str  # e.g. https://api.groq.com/openai/v1
    model: str
    api_key: str = field(repr=False)  # never in a repr, so never in a log or an error report


def _post(provider: Provider, body: dict) -> dict:
    url = provider.base_url.rstrip("/") + "/chat/completions"
    if not url.startswith("https://"):
        raise AiUnavailable(f"refusing a non-HTTPS provider: {provider.name}")
    request = urllib.request.Request(  # noqa: S310 - HTTPS checked above
        url,
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {provider.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "dwellwise-api",
        },
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:  # noqa: S310
        return json.loads(response.read())


class ChatClient:
    """``chat(messages, tools)`` returns the assistant message, the provider's name and the tokens used."""

    def __init__(self, providers: list[Provider], post=_post):
        self.providers = providers
        self.post = post

    def __call__(self, messages: list[dict], tools: list[dict]) -> dict:
        failures = []
        for provider in self.providers:
            body = {"model": provider.model, "messages": messages, "tools": tools, "temperature": 0}
            try:
                answer = self.post(provider, body)
                message = answer["choices"][0]["message"]
                tokens = int((answer.get("usage") or {}).get("total_tokens") or 0)
            except urllib.error.HTTPError as exc:
                AI_MODEL_CALLS.labels(provider.name, "failed").inc()
                if exc.code == 429 or exc.code >= 500:
                    failures.append(f"{provider.name}: HTTP {exc.code}")
                    continue
                raise AiUnavailable(f"{provider.name} refused the request: HTTP {exc.code}") from exc
            except (urllib.error.URLError, TimeoutError, ValueError) as exc:
                AI_MODEL_CALLS.labels(provider.name, "failed").inc()
                failures.append(f"{provider.name}: {type(exc).__name__}")
                continue
            except (KeyError, IndexError, TypeError, AttributeError):
                AI_MODEL_CALLS.labels(provider.name, "failed").inc()
                failures.append(f"{provider.name}: malformed reply")
                continue
            AI_MODEL_CALLS.labels(provider.name, "ok").inc()
            AI_TOKENS.labels(provider.name).inc(tokens)
            return {"message": message, "provider": provider.name, "tokens": tokens}
        raise AiUnavailable("; ".join(failures) or "no AI provider is configured")
