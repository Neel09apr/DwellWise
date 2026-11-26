from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from .. import building, stats
from ..db import get_conn
from ..months import MonthRange
from ..place import AnyPlace, CountyOrIreland
from ..schemas import ApplicationStats, CommencementStats, ErrorBody

router = APIRouter(prefix="/v1/stats", tags=["stats"])

Conn = Annotated[object, Depends(get_conn)]


@router.get(
    "/applications",
    response_model=ApplicationStats,
    responses={404: {"model": ErrorBody}, 422: {"model": ErrorBody}},
)
def application_stats(
    conn: Conn,
    place: CountyOrIreland,
    months: MonthRange,
    residential: Annotated[
        bool | None, Query(description="true: only applications that state dwellings")
    ] = None,
) -> ApplicationStats:
    """Planning applications received each month, counted by their current decision class."""
    return stats.application_stats(conn, place, residential, months)


@router.get(
    "/commencements",
    response_model=CommencementStats,
    responses={404: {"model": ErrorBody}, 422: {"model": ErrorBody}},
)
def commencement_stats(conn: Conn, place: AnyPlace, months: MonthRange) -> CommencementStats:
    """Homes whose construction started each month, from commencement notices, and the newest schemes."""
    return building.commencement_stats(conn, place, months)
