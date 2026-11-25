from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from .. import developments
from ..db import get_conn
from ..place import CountyOrIreland
from ..schemas import Developments, ErrorBody

router = APIRouter(prefix="/v1/map", tags=["map"])

Conn = Annotated[object, Depends(get_conn)]


@router.get("/developments", response_model=Developments, responses={404: {"model": ErrorBody}})
def development_map(conn: Conn, place: CountyOrIreland) -> Developments:
    """GeoJSON of schemes of five homes or more started or applied for in the last 12 months."""
    return developments.developments(conn, place)
