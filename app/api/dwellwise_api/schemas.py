from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


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
    newest_received: date | None  # the source lags: its newest application, not our capture time
    attribution: str
    totals: DecisionCounts
    months: list[MonthCounts]
    counties: list[CountyCounts]


class HomesCount(BaseModel):
    notices: int
    homes: int


class CommencementMonth(HomesCount):
    month: str  # YYYY-MM, by commencement date


class Scheme(BaseModel):
    """A commencement notice for five homes or more. Smaller ones are counted, never listed."""

    notice_number: str
    project_name: str | None
    settlement: str | None
    county: str
    local_authority: str
    homes: int
    scheme_homes: int | None
    commenced: date | None
    expected_end: date | None
    planning_ref: str | None


class CommencementStats(BaseModel):
    county: str | None
    settlement: str | None  # CSO code
    from_month: str
    to_month: str
    captured_at: datetime | None
    newest_submitted: date | None
    attribution: str
    totals: HomesCount
    last_7_days: HomesCount  # notices received in the week before the capture
    months: list[CommencementMonth]
    recent_schemes: list[Scheme]


class DevelopmentProperties(BaseModel):
    kind: str  # "started" (commencement notice) or "applied" (planning application)
    label: str | None  # the scheme's name, for started schemes that give one
    authority: str
    homes: int
    day: date  # start date (started) or date received (applied)
    settlement: str | None
    status: str | None  # decision class, for applications
    reference: str | None  # planning reference


class PointGeometry(BaseModel):
    type: str = "Point"
    coordinates: list[float]  # [longitude, latitude], WGS84


class DevelopmentFeature(BaseModel):
    type: str = "Feature"
    geometry: PointGeometry
    properties: DevelopmentProperties


class UnitReporting(BaseModel):
    authority: str
    share: int  # percent of its applications in the period that state a number of units


class Developments(BaseModel):
    """GeoJSON: schemes of five homes or more, started or applied for in the last 12 months."""

    type: str = "FeatureCollection"
    county: str | None
    min_homes: int
    attribution: list[str]
    # Councils that rarely or never state units: their applications cannot appear on the map.
    sparse_units: list[UnitReporting]
    features: list[DevelopmentFeature]


class PriceMonth(BaseModel):
    month: str  # YYYY-MM, by the month the deed was executed
    sales: int | None  # None where the CSO suppresses a small count
    median: int | None  # euro
    new_sales: int | None  # new homes only
    new_median: int | None


class PriceArea(BaseModel):
    kind: str  # "eircode" (routing area) or "region" (CSO county, council area or Ireland)
    code: str
    name: str
    latest: PriceMonth | None  # the newest month with a median for all homes
    sales_12_months: int  # sales in the 12 months up to the newest month, suppressed months counted as 0
    months: list[PriceMonth]


class Prices(BaseModel):
    """What homes sold for in an area, from CSO stamp duty statistics. Never the value of a site."""

    county: str | None
    settlement: str | None
    basis: str  # how the area was chosen, in words
    captured_at: datetime | None
    attribution: str
    areas: list[PriceArea]


class CostLine(BaseModel):
    item: str
    amount: int  # euro, rounded
    working: str  # the arithmetic, in words: "8 homes × 110 m² × €2,800 per m²"


class Costs(BaseModel):
    """A development cost estimate from the user's own figures. Excludes VAT; never a site's value."""

    homes: int
    floor_area_m2: float  # all homes together
    lines: list[CostLine]
    total: int  # the sum of the lines
    per_home: int
    note: str


class Turn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=1000)


class Question(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    settlement: str | None = Field(default=None, pattern=r"^\d{1,6}$")
    history: list[Turn] = Field(default_factory=list, max_length=4)  # the conversation so far


class AssistantStatus(BaseModel):
    enabled: bool  # false: no key, or the kill switch is on; the web app hides the question box


class Answer(BaseModel):
    """A model's answer whose every number was found in DwellWise's data, or a refusal saying it was not."""

    answer: str
    grounded: bool  # false: the answer failed the check and was replaced by a refusal
    tools: list[str]  # the tools the model called, in order
    cached: bool
    shortlists: list[Shortlist] = []  # code-ranked tables the answer explains; never beside a refusal


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


class ShortlistTown(BaseModel):
    code: str
    name: str
    granted: int  # residential applications inside the boundary, over the brief's years
    refused: int
    pending: int
    homes_started: int  # in the months from started_since
    protected_within_1km: int  # protected sites touching the town or within 1 km
    price_area: str | None  # the Eircode routing area most of the town's notices carry
    median_price: int | None  # euro, all homes, the area's newest month with a median
    price_month: str | None


class Shortlist(BaseModel):
    """A county's towns side by side, sorted by one stated column. Evidence about towns, never a score."""

    county: str
    sort: str
    sorted_by: str  # the sort, in words
    towns_in_county: int
    applications_since: date
    started_since: str  # YYYY-MM, the first of the last 12 months
    towns: list[ShortlistTown]  # at most five
    note: str
    attribution: list[str]


Answer.model_rebuild()
