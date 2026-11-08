import json

import pytest

from dwellwise_pipeline.arcgis import FetchError, fetch_features, http_get


def feature(n: int) -> dict:
    return {"type": "Feature", "properties": {"ID": n}, "geometry": {"type": "Point", "coordinates": [0, 0]}}


class FakeService:
    def __init__(self, responses: list):
        self.responses = list(responses)
        self.urls: list[str] = []

    def __call__(self, url: str) -> bytes:
        self.urls.append(url)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return json.dumps(response).encode()


def no_sleep(_seconds: float) -> None:
    pass


def test_pages_until_the_service_says_there_is_no_more():
    service = FakeService(
        [
            {"features": [feature(1), feature(2)], "exceededTransferLimit": True},
            {"features": [feature(3)], "properties": {"exceededTransferLimit": False}},
        ]
    )
    result = fetch_features(
        "https://example.test/0", ["ID"], "ID", opener=service, sleep=no_sleep, page_size=2
    )
    assert [f["properties"]["ID"] for f in result["features"]] == [1, 2, 3]
    assert "resultOffset=0" in service.urls[0] and "resultOffset=2" in service.urls[1]
    assert "orderByFields=ID" in service.urls[0]


def test_a_pending_or_error_body_is_retried_and_never_returned():
    pending = {"message": "Up to date download file is being generated.", "status": "Pending"}
    service = FakeService([pending, {"error": {"code": 500}}, {"features": [feature(1)]}])
    result = fetch_features("https://example.test/0", ["ID"], "ID", opener=service, sleep=no_sleep)
    assert len(result["features"]) == 1
    assert len(service.urls) == 3


def test_gives_up_after_three_bad_answers():
    service = FakeService([{"status": "Pending"}, OSError("reset"), ValueError("bad json")])
    with pytest.raises(FetchError, match="after 3 attempts"):
        fetch_features("https://example.test/0", ["ID"], "ID", opener=service, sleep=no_sleep)


def test_refuses_plain_http():
    with pytest.raises(FetchError, match="non-HTTPS"):
        http_get("http://example.test/")
