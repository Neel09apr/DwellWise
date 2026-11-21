from pathlib import Path

import pytest

from ops.probe import CHECKS, Check, http_get, main, probe

CHECK = Check("API down", "/health", 1.0, "docs/runbooks/api-down.md")


class Service:
    """Answers with the given (status, body) or raises, one per call."""

    def __init__(self, *answers):
        self.answers = list(answers)
        self.urls = []

    def __call__(self, url):
        self.urls.append(url)
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer


class Clock:
    def __init__(self, *readings):
        self.readings = list(readings)

    def __call__(self):
        return self.readings.pop(0)


def no_sleep(_s):
    pass


def test_a_healthy_service_passes_on_the_first_try():
    r = probe("https://x/", CHECK, opener=Service((200, b"{}")), sleep=no_sleep, clock=Clock(0, 0.2))
    assert (r.ok, r.status, r.attempts, r.slow, r.detail) == (True, 200, 1, False, "")


def test_a_cold_start_is_retried_not_reported():
    service = Service(TimeoutError("timed out"), (200, b"{}"))
    r = probe("https://x", CHECK, opener=service, sleep=no_sleep, clock=Clock(0, 60, 0, 0.3))
    assert (r.ok, r.attempts) == (True, 2)
    assert service.urls == ["https://x/health", "https://x/health"]


def test_three_failures_are_down_with_the_last_status_and_body():
    service = Service((503, b"a"), (503, b"b"), (503, b'{"status":"stale"}'))
    r = probe("https://x", CHECK, opener=service, sleep=no_sleep, clock=Clock(0, 1, 0, 1, 0, 1))
    assert (r.ok, r.status, r.attempts, r.detail) == (False, 503, 3, '{"status":"stale"}')


def test_unreachable_is_status_zero():
    service = Service(ConnectionRefusedError("refused"), OSError("x"), OSError("dns"))
    r = probe("https://x", CHECK, opener=service, sleep=no_sleep, clock=Clock(0, 1, 0, 1, 0, 1))
    assert (r.ok, r.status) == (False, 0)
    assert r.detail.startswith("OSError")


def test_slow_is_reported_but_is_not_down():
    r = probe("https://x", CHECK, opener=Service((200, b"{}")), sleep=no_sleep, clock=Clock(0, 1.5))
    assert (r.ok, r.slow) == (True, True)


def test_every_check_has_a_runbook_that_exists():
    root = Path(__file__).resolve().parents[1]
    assert all((root / c.runbook).is_file() for c in CHECKS)


def test_the_cli_refuses_plain_http():
    assert main(["probe.py", "http://insecure"]) == 2


def test_the_fetcher_itself_refuses_plain_http():
    with pytest.raises(ValueError, match="non-HTTPS"):
        http_get("http://insecure/health")
