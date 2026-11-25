from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends

from .. import prices
from ..db import get_conn
from ..place import AnyPlace
from ..schemas import ErrorBody, Prices

router = APIRouter(prefix="/v1", tags=["prices"])

Conn = Annotated[object, Depends(get_conn)]


@router.get(
    "/prices", response_model=Prices, responses={404: {"model": ErrorBody}, 422: {"model": ErrorBody}}
)
def sale_prices(conn: Conn, place: AnyPlace) -> Prices:
    """Median sale prices and sales by month for the area around a town, a county or Ireland (CSO)."""
    return prices.prices(conn, place, date.today())
