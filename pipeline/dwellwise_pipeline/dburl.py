"""DATABASE_URL as given, with a raw password made safe for libpq."""

from __future__ import annotations

from urllib.parse import quote


def normalise(url: str) -> str:
    """Percent-encode the password so characters like @ or / cannot break the URL.

    The last @ separates credentials from host. A password that already holds a
    % escape is left alone. Mirrors app/api's normalise_database_url.
    """
    scheme, sep, rest = url.partition("://")
    if not sep or "@" not in rest:
        return url
    credentials, host = rest.rsplit("@", 1)
    user, colon, password = credentials.partition(":")
    if not colon or "%" in password:
        return url
    return f"{scheme}://{user}:{quote(password, safe='')}@{host}"
