"""Print DATABASE_URL with a raw password percent-encoded (it may contain @ or /).

Used by .github/workflows/observability.yml to give Terraform's pg backend a URL
libpq can parse. Same rule as app/api and pipeline: the last @ ends the
credentials; a password that already holds a % escape is left alone.
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


if __name__ == "__main__":
    print(normalise(os.environ["DATABASE_URL"]))  # noqa: T201 - read by the workflow, masked there
