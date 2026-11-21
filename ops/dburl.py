"""Print DATABASE_URL with a raw password percent-encoded (it may contain @ or /).

Used by the Terraform workflows (observability, github-settings,
supabase-settings) to give the pg state backend a URL it can parse. Same rule as
app/api and pipeline: the last @ ends the credentials; a password that already
holds a % escape is left alone.

The backend does not try TLS unless told to, and the database enforces SSL
(terraform/stacks/supabase), so sslmode=require is added when the URL sets none.
"""

from __future__ import annotations

import os
from urllib.parse import quote


def normalise(url: str) -> str:
    scheme, sep, rest = url.partition("://")
    if not sep or "@" not in rest:
        return url
    credentials, host = rest.rsplit("@", 1)
    user, colon, password = credentials.partition(":")
    if not colon or "%" in password:
        return url
    return f"{scheme}://{user}:{quote(password, safe='')}@{host}"


def for_terraform(url: str) -> str:
    """normalise(url), plus sslmode=require unless the URL already chooses a mode."""
    url = normalise(url)
    if "sslmode=" in url:
        return url
    return f"{url}{'&' if '?' in url else '?'}sslmode=require"


if __name__ == "__main__":
    print(for_terraform(os.environ["DATABASE_URL"]))  # noqa: T201 - read by the workflow, masked there
