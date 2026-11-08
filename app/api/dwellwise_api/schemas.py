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
