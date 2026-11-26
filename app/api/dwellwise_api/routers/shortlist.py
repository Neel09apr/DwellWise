from __future__ import annotations

from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query

from .. import shortlist as feature
from ..db import get_conn
from ..place import CountyRequired
from ..schemas import ErrorBody, Shortlist

router = APIRouter(prefix="/v1", tags=["shortlist"])

Conn = Annotated[object, Depends(get_conn)]


@router.get(
    "/shortlist",
    response_model=Shortlist,
    responses={404: {"model": ErrorBody}, 422: {"model": ErrorBody}},
)
def county_shortlist(
    conn: Conn,
    place: CountyRequired,
    sort: Annotated[Literal["started", "granted", "protected", "price"], Query()] = "started",
) -> Shortlist:
    """A county's top five towns by one stated column: planning precedents, homes started, protected
    sites within 1 km and the area's median sale price. Evidence about towns, never a score."""
    return feature.shortlist(conn, place, sort, date.today())
