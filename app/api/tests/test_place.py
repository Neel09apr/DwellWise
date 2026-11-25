"""Place rules against an in-memory gazetteer, and the HTTP errors they end requests with."""

import pytest
from fastapi.testclient import TestClient

from dwellwise_api.config import Settings
from dwellwise_api.db import get_conn
from dwellwise_api.main import create_app
from dwellwise_api.place import REFRESH_SECONDS, PlaceError

from .fakes import memory_places


def test_ireland_is_every_county_and_a_county_is_normalised():
    places = memory_places()
    assert places.resolve(None).kind == "ireland"
    assert places.resolve(None).counties == ("CORK", "KILDARE", "MAYO", "MEATH")
    kildare = places.resolve(None, county=" kildare ")
    assert (kildare.kind, kildare.county, kildare.counties, kildare.asked_county) == (
        "county", "KILDARE", ("KILDARE",), "KILDARE",
    )  # fmt: skip


def test_a_settlement_carries_its_own_county():
    athy = memory_places().resolve(None, settlement="1")
    assert (athy.kind, athy.settlement, athy.settlement_name, athy.county) == (
        "settlement",
        "1",
        "Athy",
        "KILDARE",
    )
    assert athy.asked_county is None  # responses echo what was asked: a settlement, not a county


def test_a_county_and_a_settlement_together_are_refused_even_when_they_agree():
    with pytest.raises(PlaceError) as caught:
        memory_places().resolve(None, county="kildare", settlement="1")
    assert (caught.value.status, caught.value.message) == (422, "Give a county or a settlement, not both.")


@pytest.mark.parametrize(
    ("county", "settlement", "message"),
    [("Atlantis", None, "No county is called Atlantis."), (None, "9999", "No settlement has the code 9999.")],
)
def test_unknown_places_are_404s(county, settlement, message):
    with pytest.raises(PlaceError) as caught:
        memory_places().resolve(None, county=county, settlement=settlement)
    assert (caught.value.status, caught.value.message) == (404, message)


def test_the_gazetteer_is_read_once_and_again_after_an_hour():
    now = [0.0]
    places = memory_places(clock=lambda: now[0])
    places.resolve(None, county="cork")
    places.resolve(None, settlement="3")
    assert len(places.loads) == 1
    now[0] = REFRESH_SECONDS - 1
    places.resolve(None)
    assert len(places.loads) == 1
    now[0] = REFRESH_SECONDS
    places.resolve(None)
    assert len(places.loads) == 2


@pytest.fixture
def offline():
    app = create_app(Settings())
    app.dependency_overrides[get_conn] = lambda: None
    app.state.places = memory_places()
    with TestClient(app) as c:
        yield c


BOTH = "Give a county or a settlement, not both."


@pytest.mark.parametrize(
    ("path", "params", "status", "message"),
    [
        ("/v1/stats/commencements", {"county": "kildare", "settlement": "3"}, 422, BOTH),
        ("/v1/prices", {"county": "kildare", "settlement": "3"}, 422, BOTH),
        ("/v1/map/developments", {"county": "Atlantis"}, 404, "No county is called Atlantis."),
        ("/v1/stats/applications", {"county": "Atlantis"}, 404, "No county is called Atlantis."),
        ("/v1/prices", {"settlement": "9999"}, 404, "No settlement has the code 9999."),
        ("/v1/counties/Atlantis/settlements", {}, 404, "No county is called Atlantis."),
        ("/v1/settlements", {"q": "ath", "county": "Atlantis"}, 404, "No county is called Atlantis."),
        ("/v1/settlements/9999", {}, 404, "No settlement has the code 9999."),
        ("/v1/settlements/9999/brief", {}, 404, "No settlement has the code 9999."),
    ],
)
def test_every_place_scoped_endpoint_ends_a_bad_place_the_same_way(offline, path, params, status, message):
    response = offline.get(path, params=params)
    assert response.status_code == status
    assert response.json()["error"]["message"] == message


def test_one_pattern_for_settlement_codes_everywhere(offline):
    for path in ("/v1/settlements/abc", "/v1/settlements/abc/brief"):
        assert offline.get(path).status_code == 422
    assert offline.get("/v1/prices", params={"settlement": "abc"}).status_code == 422
