from fastapi.testclient import TestClient

from dwellwise_api.config import Settings
from dwellwise_api.main import create_app


def test_health_needs_nothing(client):
    response = client.get("/health")
    assert response.status_code == 200 and response.json() == {"status": "ok"}
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    assert response.headers["x-request-id"]


def test_ready_is_unavailable_without_a_database(client):
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "checks": {"database": "not configured"}}


def test_api_errors_share_one_shape(client):
    assert client.get("/v1/settlements", params={"q": "athy"}).json() == {
        "error": {"code": "service_unavailable", "message": "The database is not configured."}
    }


def test_invalid_input_is_a_422_in_the_same_shape():
    from dwellwise_api.db import get_conn

    app = create_app(Settings())
    app.dependency_overrides[get_conn] = lambda: None  # validation is checked without a database
    with TestClient(app) as c:
        response = c.get("/v1/settlements", params={"q": "x" * 81})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "unprocessable_content"
    assert response.json()["error"]["message"].startswith("q:")


def test_metrics_label_routes_by_template_not_raw_path(client):
    client.get("/v1/settlements/12345")
    body = client.get("/metrics").text
    assert 'route="/v1/settlements/{code}"' in body
    assert "12345" not in body


def test_metrics_can_require_a_token():
    with TestClient(create_app(Settings(metrics_token="s3cret"))) as c:
        assert c.get("/metrics").status_code == 401
        assert c.get("/metrics", headers={"Authorization": "Bearer s3cret"}).status_code == 200


def test_the_web_app_is_served_for_client_routes_but_not_for_api_routes(tmp_path):
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<!doctype html><title>app</title>", encoding="utf-8")
    (tmp_path / "assets" / "app-1a2b.js").write_text("console.log(1)", encoding="utf-8")
    (tmp_path.parent / "secret.txt").write_text("nope", encoding="utf-8")
    with TestClient(create_app(Settings(web_dist=tmp_path))) as c:
        assert "<title>app</title>" in c.get("/settlements/123").text
        asset = c.get("/assets/app-1a2b.js")
        assert "immutable" in asset.headers["cache-control"]
        assert c.get("/v1/nothing").status_code == 404
        assert "nope" not in c.get("/../secret.txt").text
