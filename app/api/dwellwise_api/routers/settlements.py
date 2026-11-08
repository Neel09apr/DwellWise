from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from .. import services
from ..db import get_conn
from ..schemas import ErrorBody, SettlementDetail, SettlementSummary

router = APIRouter(prefix="/v1/settlements", tags=["settlements"])

Conn = Annotated[object, Depends(get_conn)]


@router.get("", response_model=list[SettlementSummary])
def search_settlements(
    conn: Conn,
    q: Annotated[str, Query(min_length=1, max_length=80, description="Part of a settlement name")],
    county: Annotated[str | None, Query(max_length=40, description="Limit to one county")] = None,
    limit: Annotated[int, Query(ge=1, le=25)] = 10,
) -> list[SettlementSummary]:
    """Settlements whose name contains the query; exact and prefix matches first."""
    return services.search(conn, q, county, limit)


@router.get("/{code}", response_model=SettlementDetail, responses={404: {"model": ErrorBody}})
def get_settlement(
    conn: Conn,
    code: Annotated[str, Path(pattern=r"^[0-9A-Za-z_-]{1,20}$", description="CSO settlement code")],
) -> SettlementDetail:
    found = services.detail(conn, code)
    if found is None:
        raise HTTPException(404, f"No settlement has the code {code}.")
    return found
