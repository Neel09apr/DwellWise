"""The cost estimate: plain arithmetic from the user's figures, shown line by line. No database."""

import pytest
from fastapi.testclient import TestClient

from dwellwise_api.config import Settings
from dwellwise_api.costs import Inputs, estimate
from dwellwise_api.main import create_app

SCHEME = Inputs(
    homes=8,
    floor_area_m2=110,
    build_cost_per_m2=2800,
    contribution=117,
    contribution_basis="per_m2",
    fees_pct=10,
    contingency_pct=5,
    finance_rate_pct=8,
    finance_months=18,
)


def amounts(costs) -> dict[str, int]:
    return {line.item: line.amount for line in costs.lines}


def test_every_line_is_worked_from_the_inputs():
    costs = estimate(SCHEME)
    # 880 m2: build 2,464,000; contributions 102,960; fees 246,400; contingency 123,200
    # finance: 2,936,560 / 2 x 8% x 18/12 = 176,193.6
    assert amounts(costs) == {
        "Build": 2_464_000,
        "Development contributions": 102_960,
        "Professional fees": 246_400,
        "Contingency": 123_200,
        "Finance": 176_194,
    }
    assert costs.total == sum(amounts(costs).values()) == 3_112_754
    assert costs.per_home == 389_094
    assert costs.floor_area_m2 == 880
    working = {line.item: line.working for line in costs.lines}
    assert working["Build"] == "8 homes × 110 m² × €2,800 per m²"
    assert working["Development contributions"] == "880 m² × €117 per m²"
    assert working["Finance"] == "8% a year for 18 months on half of €2,936,560, as if drawn evenly"


def test_a_charge_per_home_multiplies_by_homes_not_floor_area():
    costs = estimate(Inputs(**{**SCHEME.__dict__, "contribution": 9000, "contribution_basis": "per_home"}))
    assert amounts(costs)["Development contributions"] == 72_000
    assert (
        dict((x.item, x.working) for x in costs.lines)["Development contributions"]
        == "8 homes × €9,000 per home"
    )


def test_land_is_a_line_only_when_given_and_is_financed():
    without = estimate(SCHEME)
    with_land = estimate(Inputs(**{**SCHEME.__dict__, "land": 400_000}))
    assert "Land" not in amounts(without)
    assert amounts(with_land)["Land"] == 400_000
    assert amounts(with_land)["Finance"] - amounts(without)["Finance"] == 24_000  # 400,000 / 2 x 8% x 1.5


def test_no_finance_and_no_extras_leave_just_build_and_contributions():
    costs = estimate(Inputs(**{**SCHEME.__dict__, "fees_pct": 0, "contingency_pct": 0, "finance_months": 0}))
    assert costs.total == 2_464_000 + 102_960


@pytest.fixture
def client():
    with TestClient(create_app(Settings())) as c:  # no database: the estimate never reads one
        yield c


PARAMS = {
    "homes": 8, "floor_area_m2": 110, "build_cost_per_m2": 2800, "contribution": 117,
    "contribution_basis": "per_m2", "fees_pct": 10, "contingency_pct": 5, "finance_rate_pct": 8,
    "finance_months": 18,
}  # fmt: skip


def test_the_endpoint_answers_with_the_lines_and_says_what_it_leaves_out(client):
    body = client.get("/v1/costs", params=PARAMS).json()
    assert body["total"] == 3_112_754 and body["per_home"] == 389_094
    assert body["note"].startswith("Excludes VAT.")


@pytest.mark.parametrize(
    "bad",
    [{"homes": 0}, {"contribution_basis": "per_acre"}, {"fees_pct": -1}, {"build_cost_per_m2": 0}],
)
def test_figures_out_of_range_are_422s(client, bad):
    response = client.get("/v1/costs", params={**PARAMS, **bad})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "unprocessable_content"


def test_every_figure_but_land_is_required(client):
    params = {k: v for k, v in PARAMS.items() if k != "fees_pct"}
    assert client.get("/v1/costs", params=params).status_code == 422
