from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path

from .. import services
from ..db import get_conn
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
def county_settlements(
    conn: Conn,
    name: Annotated[str, Path(pattern=r"^[A-Za-z][A-Za-z \-]{1,30}$", description="County name, any case")],
) -> list[SettlementSummary]:
    """The county's settlements, A to Z."""
    found = services.county_settlements(conn, name)
    if found is None:
        raise HTTPException(404, f"No county is called {name}.")
    return found
