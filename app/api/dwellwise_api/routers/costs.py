from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Query

from .. import costs
from ..schemas import Costs, ErrorBody

router = APIRouter(prefix="/v1", tags=["costs"])


@router.get("/costs", response_model=Costs, responses={422: {"model": ErrorBody}})
def cost_estimate(
    homes: Annotated[int, Query(ge=1, le=1000, description="Number of homes")],
    floor_area_m2: Annotated[float, Query(gt=0, le=2000, description="Floor area of each home, m²")],
    build_cost_per_m2: Annotated[float, Query(gt=0, le=50_000, description="Build cost, euro per m²")],
    contribution: Annotated[
        float, Query(ge=0, le=1_000_000, description="Development contribution, euro per m² or per home")
    ],
    contribution_basis: Annotated[
        Literal["per_m2", "per_home"], Query(description="How the council charges")
    ],
    fees_pct: Annotated[float, Query(ge=0, le=100, description="Professional fees, % of build")],
    contingency_pct: Annotated[float, Query(ge=0, le=100, description="Contingency, % of build")],
    finance_rate_pct: Annotated[float, Query(ge=0, le=50, description="Interest, % a year")],
    finance_months: Annotated[int, Query(ge=0, le=240, description="Months the money is borrowed for")],
    land: Annotated[
        float, Query(ge=0, le=1_000_000_000, description="Land cost, euro; omit to leave out")
    ] = 0,
) -> Costs:
    """What a scheme might cost to build, from your own figures, each line with its working. Excludes VAT."""
    return costs.estimate(
        costs.Inputs(
            homes=homes,
            floor_area_m2=floor_area_m2,
            build_cost_per_m2=build_cost_per_m2,
            contribution=contribution,
            contribution_basis=contribution_basis,
            fees_pct=fees_pct,
            contingency_pct=contingency_pct,
            finance_rate_pct=finance_rate_pct,
            finance_months=finance_months,
            land=land,
        )
    )
