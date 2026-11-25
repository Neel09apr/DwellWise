from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from .. import developments
from ..db import get_conn
from ..schemas import Developments, ErrorBody

router = APIRouter(prefix="/v1/map", tags=["map"])

Conn = Annotated[object, Depends(get_conn)]


@router.get("/developments", response_model=Developments, responses={404: {"model": ErrorBody}})
def development_map(
    conn: Conn,
    county: Annotated[
        str | None,
        Query(pattern=r"^[A-Za-z][A-Za-z \-]{1,30}$", description="County name; none means Ireland"),
    ] = None,
) -> Developments:
    """GeoJSON of schemes of five homes or more started or applied for in the last 12 months."""
    found = developments.developments(conn, county)
    if found is None:
        raise HTTPException(404, f"No county is called {county}.")
    return found
