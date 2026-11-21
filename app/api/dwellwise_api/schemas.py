from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorBody(BaseModel):
    error: ErrorDetail


class Health(BaseModel):
    status: str


class Ready(BaseModel):
    status: str
    checks: dict[str, str]


class County(BaseModel):
    name: str
    settlements: int


class SettlementSummary(BaseModel):
    code: str
    name: str
    county: str | None


class SourceInfo(BaseModel):
    name: str
    captured_at: datetime
    attribution: str


class SettlementDetail(SettlementSummary):
    latitude: float
    longitude: float
    area_km2: float
    sources: list[SourceInfo]


class DecisionCounts(BaseModel):
    """Applications by current decision class. "other" covers invalid, exempt and split decisions."""

    granted: int
    refused: int
    pending: int
    withdrawn: int
    other: int
    total: int


class MonthCounts(DecisionCounts):
    month: str  # YYYY-MM, by date received


class CountyCounts(DecisionCounts):
    county: str


class ApplicationStats(BaseModel):
    county: str | None  # None means all of Ireland
    residential: bool | None  # None means all applications
    from_month: str
    to_month: str
    captured_at: datetime | None
    attribution: str
    totals: DecisionCounts
    months: list[MonthCounts]
    counties: list[CountyCounts]


class PrecedentApplication(BaseModel):
    """One planning application, as the council published it. Never an applicant name or address."""

    authority: str
    application_number: str
    received: date
    decided: date | None
    decision: str | None  # the council's own wording
    decision_class: str
    units_stated: int | None


class Precedents(BaseModel):
    """Residential applications (stating new dwellings) inside the settlement boundary."""

    since: date
    years: int
    residential: DecisionCounts
    all_applications: int  # every application in the boundary, for context
    recent: list[PrecedentApplication]
    captured_at: datetime | None
    attribution: str


class ProtectedSite(BaseModel):
    """A SAC, SPA or NHA near the settlement, measured boundary to boundary."""

    designation: str  # SAC | SPA | NHA
    site_code: str
    name: str
    url: str | None  # the site's NPWS page
    distance_m: int  # shortest distance between the site and the settlement boundary; 0 when they touch
    band: str  # "touches" | "1km" | "5km"


class ProtectedSites(BaseModel):
    """Protected sites within radius_m of the settlement boundary, nearest first."""

    radius_m: int
    sites: list[ProtectedSite]
    captured_at: datetime | None
    attribution: str


class Brief(BaseModel):
    code: str
    precedents: Precedents
    protected: ProtectedSites
    pending: list[str]  # sections whose data source has not landed yet
