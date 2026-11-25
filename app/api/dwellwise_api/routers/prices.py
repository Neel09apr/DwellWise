from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from .. import prices
from ..db import get_conn
from ..schemas import ErrorBody, Prices

router = APIRouter(prefix="/v1", tags=["prices"])

Conn = Annotated[object, Depends(get_conn)]


@router.get("/prices", response_model=Prices, responses={404: {"model": ErrorBody}})
def sale_prices(
    conn: Conn,
    county: Annotated[
        str | None,
        Query(pattern=r"^[A-Za-z][A-Za-z \-]{1,30}$", description="County name; none means Ireland"),
    ] = None,
    settlement: Annotated[str | None, Query(pattern=r"^\d{1,6}$", description="CSO settlement code")] = None,
) -> Prices:
    """Median sale prices and sales by month for the area around a town, a county or Ireland (CSO)."""
    found = prices.prices(conn, county, settlement, date.today())
    if found is None:
        raise HTTPException(404, "No such county or settlement.")
    return found
