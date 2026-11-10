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
        )
