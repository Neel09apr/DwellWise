import pytest
import sentry_sdk
from fastapi.testclient import TestClient
from sentry_sdk.transport import Transport

from dwellwise_api.config import Settings
from dwellwise_api.main import create_app


class Collect(Transport):
    """Keeps events in memory instead of sending them."""

    def __init__(self, options=None):
        super().__init__(options)
        self.events: list[dict] = []

    def capture_envelope(self, envelope):
        self.events += [item.payload.json for item in envelope.items if item.type == "event"]


@pytest.fixture
def tracked(monkeypatch):
    transport = Collect()
    real_init = sentry_sdk.init
    monkeypatch.setattr(sentry_sdk, "init", lambda **kw: real_init(transport=transport, **kw))
    yield transport
    sentry_sdk.get_client().close()
    real_init()  # back to a disabled client for the other tests


def _boom_app(settings: Settings):
    app = create_app(settings)

    @app.get("/v1/boom")
    async def boom():
        raise RuntimeError("database fell over")

    return app


def test_an_unhandled_error_reaches_sentry_without_secrets(tracked):
    app = _boom_app(Settings(sentry_dsn="https://key@o0.ingest.sentry.io/0", release="abc123"))
    with TestClient(app, raise_server_exceptions=False) as c:
        response = c.get("/v1/boom", headers={"Authorization": "Bearer secret-token"})
    assert response.status_code == 500
    assert "database fell over" not in response.text
    sentry_sdk.flush()
    [event] = tracked.events
    assert event["exception"]["values"][-1]["value"] == "database fell over"
    assert event["release"] == "abc123"
    assert "secret-token" not in str(event)


def test_error_tracking_is_off_without_a_dsn(tracked):
    with TestClient(_boom_app(Settings()), raise_server_exceptions=False) as c:
        assert c.get("/v1/boom").status_code == 500
    sentry_sdk.flush()
    assert tracked.events == []


def test_settings_read_the_dsn_and_the_deployed_commit():
    settings = Settings.from_env(
        {"DWELLWISE_DOTENV": "missing", "SENTRY_DSN": "https://k@x/1", "RENDER_GIT_COMMIT": "f00"}
    )
    assert (settings.sentry_dsn, settings.release) == ("https://k@x/1", "f00")
