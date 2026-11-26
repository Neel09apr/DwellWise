"""Place: Ireland, one county or one settlement. Exactly one per request.

Every endpoint that is scoped to a place takes a resolved ``Place`` from one of the
FastAPI dependencies below and never sees the raw query or path text. Resolving
normalises a county's name, checks that the county or settlement exists, gives a
settlement its own county, and refuses a county and a settlement together. Failures
end the request with the API's error shape: 404 for a place that does not exist,
422 for a request that names two.

The counties and settlements come from an in-memory gazetteer loaded through a
``load`` function (SQL in production, a list in tests) and reloaded when it is an
hour old: 26 counties and under a thousand settlements, which change only when the
boundaries are reloaded. So resolving costs no database round trip, and each
feature query stays a single round trip (DESIGN.md section 13).
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Annotated

from fastapi import Depends, HTTPException, Path, Query, Request

from .db import get_conn

COUNTY_PATTERN = r"^[A-Za-z][A-Za-z \-]{1,30}$"
SETTLEMENT_PATTERN = r"^\d{1,6}$"
REFRESH_SECONDS = 3600


@dataclass(frozen=True)
class Gazetteer:
    counties: tuple[str, ...]  # canonical upper-case names, A to Z
    settlements: dict[str, tuple[str, str]] = field(default_factory=dict)  # code -> (name, county)


@dataclass(frozen=True)
class Place:
    """Ireland when both are None. A settlement always carries its own county."""

    county: str | None = None
    settlement: str | None = None
    settlement_name: str | None = None
    counties: tuple[str, ...] = ()  # the counties in scope: all of them for Ireland, else one

    @property
    def kind(self) -> str:
        return "settlement" if self.settlement else "county" if self.county else "ireland"

    @property
    def asked_county(self) -> str | None:
        """The county the request named, for responses that echo it; None for a settlement."""
        return self.county if self.kind == "county" else None


class PlaceError(Exception):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


class Places:
    """Resolves place names against a gazetteer that it loads, and reloads hourly, on demand."""

    def __init__(
        self, load: Callable[[object], Gazetteer], clock: Callable[[], float] = time.monotonic
    ) -> None:
        self._load = load
        self._clock = clock
        self._lock = threading.Lock()
        self._gazetteer: Gazetteer | None = None
        self._loaded_at = 0.0

    def _current(self, conn) -> Gazetteer:
        with self._lock:
            if self._gazetteer is None or self._clock() - self._loaded_at >= REFRESH_SECONDS:
                self._gazetteer = self._load(conn)
                self._loaded_at = self._clock()
            return self._gazetteer

    def resolve(self, conn, county: str | None = None, settlement: str | None = None) -> Place:
        if county and settlement:
            raise PlaceError(422, "Give a county or a settlement, not both.")
        gazetteer = self._current(conn)
        if not county and not settlement:
            return Place(counties=gazetteer.counties)
        if county:
            name = county.strip().upper()
            if name not in gazetteer.counties:
                raise PlaceError(404, f"No county is called {county}.")
            return Place(county=name, counties=(name,))
        found = gazetteer.settlements.get(settlement)
        if found is None:
            raise PlaceError(404, f"No settlement has the code {settlement}.")
        name, home = found
        return Place(county=home, settlement=settlement, settlement_name=name, counties=(home,))


def load_from_database(conn) -> Gazetteer:
    with conn.cursor() as cur:
        cur.execute("select name from dw.county order by name")
        counties = tuple(row[0] for row in cur.fetchall())
        cur.execute("select code, name, county from dw.settlement")
        settlements = {code: (name, county) for code, name, county in cur.fetchall()}
    return Gazetteer(counties=counties, settlements=settlements)


Conn = Annotated[object, Depends(get_conn)]
CountyQuery = Annotated[
    str | None, Query(pattern=COUNTY_PATTERN, description="County name; none means Ireland")
]
SettlementQuery = Annotated[str | None, Query(pattern=SETTLEMENT_PATTERN, description="CSO settlement code")]


def _resolve(request: Request, conn, county: str | None = None, settlement: str | None = None) -> Place:
    try:
        return request.app.state.places.resolve(conn, county, settlement)
    except PlaceError as exc:
        raise HTTPException(exc.status, exc.message) from exc


def any_place(
    request: Request, conn: Conn, county: CountyQuery = None, settlement: SettlementQuery = None
) -> Place:
    """Ireland, a county or a settlement, from the query string."""
    return _resolve(request, conn, county, settlement)


def county_or_ireland(request: Request, conn: Conn, county: CountyQuery = None) -> Place:
    """Ireland or a county, from the query string."""
    return _resolve(request, conn, county)


def county_required(
    request: Request,
    conn: Conn,
    county: Annotated[str, Query(pattern=COUNTY_PATTERN, description="County name, any case")],
) -> Place:
    """One county, from the query string; required."""
    return _resolve(request, conn, county)


def county_in_path(
    request: Request,
    conn: Conn,
    name: Annotated[str, Path(pattern=COUNTY_PATTERN, description="County name, any case")],
) -> Place:
    return _resolve(request, conn, county=name)


def settlement_in_path(
    request: Request,
    conn: Conn,
    code: Annotated[str, Path(pattern=SETTLEMENT_PATTERN, description="CSO settlement code")],
) -> Place:
    return _resolve(request, conn, settlement=code)


AnyPlace = Annotated[Place, Depends(any_place)]
CountyOrIreland = Annotated[Place, Depends(county_or_ireland)]
CountyInPath = Annotated[Place, Depends(county_in_path)]
CountyRequired = Annotated[Place, Depends(county_required)]
SettlementInPath = Annotated[Place, Depends(settlement_in_path)]
