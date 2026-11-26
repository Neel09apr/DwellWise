"""Settings from the environment, with an optional local .env file."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote


def read_dotenv(path: Path) -> dict[str, str]:
    """KEY=VALUE lines; comments and blank lines ignored. Missing file means no values."""
    if not path.is_file():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip("'\"")
    return values


def normalise_database_url(url: str) -> str:
    """Percent-encode a raw password so characters like @ or / cannot break the URL.

    The last @ separates credentials from host. A password that already holds a
    % escape is left alone.
    """
    scheme, sep, rest = url.partition("://")
    if not sep or "@" not in rest:
        return url
    credentials, host = rest.rsplit("@", 1)
    user, colon, password = credentials.partition(":")
    if not colon or "%" in password:
        return url
    return f"{scheme}://{user}:{quote(password, safe='')}@{host}"


@dataclass(frozen=True)
class Settings:
    database_url: str | None = None
    web_dist: Path | None = None
    freshness_hours: float = 48
    metrics_token: str | None = None
    sentry_dsn: str | None = None  # error tracking is off without it
    release: str | None = None  # the deployed commit; Render sets RENDER_GIT_COMMIT
    ai_api_key: str | None = None  # Groq; the assistant is off without it
    ai_base_url: str = "https://api.groq.com/openai/v1"
    ai_model: str = "openai/gpt-oss-120b"
    ai_fallback_api_key: str | None = None  # e.g. Cloudflare Workers AI, OpenAI-compatible
    ai_fallback_base_url: str | None = None
    ai_fallback_model: str | None = None
    ai_enabled: bool = True  # the kill switch: AI_ENABLED=false turns the assistant off
    ai_daily_cap: int = 800  # below Groq's free 1,000 requests a day
    ai_per_ip_hour: int = 10

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Settings:
        env = dict(os.environ if env is None else env)
        values = {**read_dotenv(Path(env.get("DWELLWISE_DOTENV", ".env"))), **env}  # real env wins
        url = values.get("DATABASE_URL") or None
        dist = values.get("WEB_DIST")
        return cls(
            database_url=normalise_database_url(url) if url else None,
            web_dist=Path(dist) if dist else None,
            freshness_hours=float(values.get("FRESHNESS_HOURS", 48)),
            metrics_token=values.get("METRICS_TOKEN") or None,
            sentry_dsn=values.get("SENTRY_DSN") or None,
            release=values.get("RENDER_GIT_COMMIT") or None,
            ai_api_key=values.get("AI_API_KEY") or None,
            ai_base_url=values.get("AI_BASE_URL") or cls.ai_base_url,
            ai_model=values.get("AI_MODEL") or cls.ai_model,
            ai_fallback_api_key=values.get("AI_FALLBACK_API_KEY") or None,
            ai_fallback_base_url=values.get("AI_FALLBACK_BASE_URL") or None,
            ai_fallback_model=values.get("AI_FALLBACK_MODEL") or None,
            ai_enabled=values.get("AI_ENABLED", "true").strip().lower() not in ("false", "0", "no", "off"),
            ai_daily_cap=int(values.get("AI_DAILY_CAP", 800)),
            ai_per_ip_hour=int(values.get("AI_PER_IP_HOUR", 10)),
        )

    def ai_providers(self) -> list:
        """The providers to try in order; empty when the assistant is switched off or has no key."""
        from .ai_client import Provider

        if not self.ai_enabled or not self.ai_api_key:
            return []
        providers = [Provider("groq", self.ai_base_url, self.ai_model, self.ai_api_key)]
        if self.ai_fallback_api_key and self.ai_fallback_base_url and self.ai_fallback_model:
            fallback = Provider(
                "fallback", self.ai_fallback_base_url, self.ai_fallback_model, self.ai_fallback_api_key
            )
            providers.append(fallback)
        return providers
