from __future__ import annotations

from datetime import datetime

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
