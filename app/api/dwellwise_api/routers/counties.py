from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from .. import services
from ..db import get_conn
from ..place import CountyInPath
from ..schemas import County, ErrorBody, SettlementSummary

router = APIRouter(prefix="/v1/counties", tags=["counties"])

Conn = Annotated[object, Depends(get_conn)]


@router.get("", response_model=list[County])
def list_counties(conn: Conn) -> list[County]:
    """Every county, with how many settlements it contains."""
    return services.counties(conn)


@router.get(
    "/{name}/settlements", response_model=list[SettlementSummary], responses={404: {"model": ErrorBody}}
)
def county_settlements(conn: Conn, place: CountyInPath) -> list[SettlementSummary]:
    """The county's settlements, A to Z."""
    return services.county_settlements(conn, place)
