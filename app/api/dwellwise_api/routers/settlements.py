from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from .. import brief as briefs
from .. import services
from ..db import get_conn
from ..place import CountyOrIreland, SettlementInPath
from ..schemas import Brief, ErrorBody, SettlementDetail, SettlementSummary

router = APIRouter(prefix="/v1/settlements", tags=["settlements"])

Conn = Annotated[object, Depends(get_conn)]


@router.get("", response_model=list[SettlementSummary], responses={404: {"model": ErrorBody}})
def search_settlements(
    conn: Conn,
    place: CountyOrIreland,
    q: Annotated[str, Query(min_length=1, max_length=80, description="Part of a settlement name")],
    limit: Annotated[int, Query(ge=1, le=25)] = 10,
) -> list[SettlementSummary]:
    """Settlements whose name contains the query; exact and prefix matches first. ``county`` limits it."""
    return services.search(conn, q, place, limit)


def _gone(place) -> HTTPException:
    return HTTPException(404, f"No settlement has the code {place.settlement}.")


@router.get("/{code}", response_model=SettlementDetail, responses={404: {"model": ErrorBody}})
def get_settlement(conn: Conn, place: SettlementInPath) -> SettlementDetail:
    found = services.detail(conn, place)
    if found is None:
        raise _gone(place)
    return found


@router.get("/{code}/brief", response_model=Brief, responses={404: {"model": ErrorBody}})
def get_brief(conn: Conn, place: SettlementInPath) -> Brief:
    """The pre-planning brief: the sections whose data has landed, and which are still pending."""
    found = briefs.brief(conn, place.settlement, date.today())
    if found is None:
        raise _gone(place)
    return found
