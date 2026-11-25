from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from .. import building, stats
from ..db import get_conn
from ..place import AnyPlace, CountyOrIreland
from ..schemas import ApplicationStats, CommencementStats, ErrorBody

router = APIRouter(prefix="/v1/stats", tags=["stats"])

Conn = Annotated[object, Depends(get_conn)]
MONTH = r"^\d{4}-(0[1-9]|1[0-2])$"
Start = Annotated[str | None, Query(alias="from", pattern=MONTH, description="First month, YYYY-MM")]
End = Annotated[str | None, Query(alias="to", pattern=MONTH, description="Last month, YYYY-MM")]


@router.get(
    "/applications",
    response_model=ApplicationStats,
    responses={404: {"model": ErrorBody}, 422: {"model": ErrorBody}},
)
def application_stats(
    conn: Conn,
    place: CountyOrIreland,
    residential: Annotated[
        bool | None, Query(description="true: only applications that state dwellings")
    ] = None,
    start: Start = None,
    end: End = None,
) -> ApplicationStats:
    """Planning applications received each month, counted by their current decision class."""
    try:
        return stats.application_stats(conn, place, residential, start, end, date.today())
    except stats.RangeError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get(
    "/commencements",
    response_model=CommencementStats,
    responses={404: {"model": ErrorBody}, 422: {"model": ErrorBody}},
)
def commencement_stats(
    conn: Conn, place: AnyPlace, start: Start = None, end: End = None
) -> CommencementStats:
    """Homes whose construction started each month, from commencement notices, and the newest schemes."""
    try:
        return building.commencement_stats(conn, place, start, end, date.today())
    except stats.RangeError as exc:
        raise HTTPException(422, str(exc)) from exc
