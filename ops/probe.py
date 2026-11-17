"""External uptime probe: checks the live service and prints one JSON line per check.

Run by .github/workflows/uptime.yml every 10 minutes. Standard library only, so
the workflow needs no installs. Each check retries, so a free-tier cold start
(about 50 s) is not reported as an outage; latency is reported separately and
never fails a check on its own.

    python ops/probe.py https://dwellwise.onrender.com
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import asdict, dataclass

USER_AGENT = "dwellwise-uptime-probe (+https://github.com/Neel09apr/DwellWise)"
ATTEMPTS = 3
TIMEOUT = 60  # seconds; a cold start takes about 50
PAUSE = 20  # seconds between attempts


@dataclass(frozen=True)
class Check:
    name: str  # also the incident title, so keep it plain
    path: str
    budget_s: float  # slower than this is reported as slow, not as down
    runbook: str


CHECKS = (
    Check("API down", "/health", 1.0, "docs/runbooks/api-down.md"),
    Check("Data stale", "/ready", 1.0, "docs/runbooks/data-stale.md"),
    Check("Dashboard API failing", "/v1/stats/applications", 0.8, "docs/runbooks/api-down.md"),
)


@dataclass
class Result:
    name: str
    path: str
    ok: bool
    status: int  # 0 when the service could not be reached
    seconds: float
    slow: bool
    attempts: int
    detail: str
    runbook: str


Opener = Callable[[str], tuple[int, bytes]]


def http_get(url: str) -> tuple[int, bytes]:
    if not url.startswith("https://"):
        raise ValueError(f"refusing a non-HTTPS URL: {url}")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})  # noqa: S310 - HTTPS checked
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:  # noqa: S310 - HTTPS checked
            return response.status, response.read(2000)
    except urllib.error.HTTPError as err:  # 4xx/5xx still carry a status and a body
        return err.code, err.read(2000)


def probe(
    base: str, check: Check, *, opener: Opener = http_get, sleep=time.sleep, clock=time.monotonic
) -> Result:
    status, seconds, detail, attempt = 0, 0.0, "", 0
    for attempt in range(1, ATTEMPTS + 1):  # noqa: B007 - the last value is reported
        start = clock()
        try:
            status, body = opener(base.rstrip("/") + check.path)
            detail = body.decode("utf-8", "replace")[:300]
        except OSError as err:  # refused, reset, DNS, timeout
            status, detail = 0, f"{type(err).__name__}: {err}"[:300]
        seconds = round(clock() - start, 3)
        if status == 200:
            break
        if attempt < ATTEMPTS:
            sleep(PAUSE)
    ok = status == 200
    return Result(
        name=check.name,
        path=check.path,
        ok=ok,
        status=status,
        seconds=seconds,
        slow=ok and seconds > check.budget_s,
        attempts=attempt,
        detail="" if ok else detail,
        runbook=check.runbook,
    )


def main(argv: list[str]) -> int:
    if len(argv) != 2 or not argv[1].startswith("https://"):
        print("usage: probe.py https://host", file=sys.stderr)  # noqa: T201
        return 2
    results = [probe(argv[1], c) for c in CHECKS]
    for r in results:
        print(json.dumps(asdict(r)))  # noqa: T201
    return 0 if all(r.ok for r in results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
