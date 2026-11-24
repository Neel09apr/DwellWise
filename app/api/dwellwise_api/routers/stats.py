from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from .. import building, stats
from ..db import get_conn
from ..schemas import ApplicationStats, CommencementStats, ErrorBody

router = APIRouter(prefix="/v1/stats", tags=["stats"])

Conn = Annotated[object, Depends(get_conn)]
MONTH = r"^\d{4}-(0[1-9]|1[0-2])$"


@router.get(
    "/applications",
    response_model=ApplicationStats,
    responses={404: {"model": ErrorBody}, 422: {"model": ErrorBody}},
)
def application_stats(
    conn: Conn,
    county: Annotated[
        str | None,
        Query(pattern=r"^[A-Za-z][A-Za-z \-]{1,30}$", description="County name; none means Ireland"),
    ] = None,
    residential: Annotated[
        bool | None, Query(description="true: only applications that state dwellings")
    ] = None,
    start: Annotated[
        str | None, Query(alias="from", pattern=MONTH, description="First month, YYYY-MM")
    ] = None,
    end: Annotated[str | None, Query(alias="to", pattern=MONTH, description="Last month, YYYY-MM")] = None,
) -> ApplicationStats:
    """Planning applications received each month, counted by their current decision class."""
    try:
        found = stats.application_stats(conn, county, residential, start, end, date.today())
    except stats.RangeError as exc:
        raise HTTPException(422, str(exc)) from exc
    if found is None:
        raise HTTPException(404, f"No county is called {county}.")
    return found


@router.get(
    "/commencements",
    response_model=CommencementStats,
    responses={404: {"model": ErrorBody}, 422: {"model": ErrorBody}},
)
def commencement_stats(
    conn: Conn,
    county: Annotated[
        str | None,
        Query(pattern=r"^[A-Za-z][A-Za-z \-]{1,30}$", description="County name; none means Ireland"),
    ] = None,
    settlement: Annotated[str | None, Query(pattern=r"^\d{1,6}$", description="CSO settlement code")] = None,
    start: Annotated[
        str | None, Query(alias="from", pattern=MONTH, description="First month, YYYY-MM")
    ] = None,
    end: Annotated[str | None, Query(alias="to", pattern=MONTH, description="Last month, YYYY-MM")] = None,
) -> CommencementStats:
    """Homes whose construction started each month, from commencement notices, and the newest schemes."""
    try:
        found = building.commencement_stats(conn, county, settlement, start, end, date.today())
    except stats.RangeError as exc:
        raise HTTPException(422, str(exc)) from exc
    if found is None:
        raise HTTPException(404, "No such county or settlement.")
    return found
