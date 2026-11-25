"""National Planning Applications (Department of Housing, ArcGIS REST). CC BY 4.0.

One point per application, published by all 31 planning authorities. Applicant
names and addresses are never requested, and validation rejects them if the
service ever sends them.

The county comes from the planning authority, not from geometry: the authority
is the council, so the mapping is exact. Decisions are worded differently by
each council; ``classify`` reduces them to five classes and reports anything it
does not recognise instead of guessing.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime

from .base import Source

LAYER = (
    "https://services.arcgis.com/NzlPQPKn5QF9v2US/arcgis/rest/services/"
    "IrishPlanningApplications/FeatureServer/0"
)

# ponytail: fixed start keeps the table near 270k rows (database limit 500 MB);
# move it, or load all years, once the size is measured.
SINCE = "2020-01-01"

AUTHORITY_COUNTY = {
    "Carlow County Council": "CARLOW",
    "Cavan County Council": "CAVAN",
    "Clare County Council": "CLARE",
    "Cork City Council": "CORK",
    "Cork County Council": "CORK",
    "Donegal County Council": "DONEGAL",
    "Dublin City Council": "DUBLIN",
    "Dun Laoghaire Rathdown County Council": "DUBLIN",
    "Fingal County Council": "DUBLIN",
    "South Dublin County Council": "DUBLIN",
    "Galway City Council": "GALWAY",
    "Galway County Council": "GALWAY",
    "Kerry County Council": "KERRY",
    "Kildare County Council": "KILDARE",
    "Kilkenny County Council": "KILKENNY",
    "Laois County Council": "LAOIS",
    "Leitrim County Council": "LEITRIM",
    "Limerick County Council": "LIMERICK",
    "Longford County Council": "LONGFORD",
    "Louth County Council": "LOUTH",
    "Mayo County Council": "MAYO",
    "Meath County Council": "MEATH",
    "Monaghan County Council": "MONAGHAN",
    "Offaly County Council": "OFFALY",
    "Roscommon County Council": "ROSCOMMON",
    "Sligo County Council": "SLIGO",
    "Tipperary County Council": "TIPPERARY",
    "Waterford City and County Council": "WATERFORD",
    "Westmeath County Council": "WESTMEATH",
    "Wexford County Council": "WEXFORD",
    "Wicklow County Council": "WICKLOW",
}

CLASSES = ("granted", "refused", "pending", "withdrawn", "other")

# The one table that turns a council's decision wording into a class. Checked in
# order; the first pattern found anywhere in the normalised text wins.
DECISION_RULES: tuple[tuple[str, str], ...] = (
    ("withdrawn", r"WITHDR"),
    ("other", r"INVALID|DECLARED INVA|EXEMPT|CERTIFICATE"),  # not a decision; the data cuts some words
    ("other", r"GRANT.*REFUS|REFUS.*GRANT|SPLIT"),  # part granted, part refused
    ("refused", r"REFUS"),
    ("granted", r"GRANT|CONDITIONAL"),  # also matches UNCONDITIONAL
    ("pending", r"ADDITIONAL INFO|FURTHER INFO|CLARIFICATION|\bAI\b"),  # AI: additional information
)

# Used only when the decision itself is blank or "N/A".
STATUS_RULES: tuple[tuple[str, str], ...] = (
    ("withdrawn", r"WITHDR"),
    ("other", r"INVALID|INCOMPLET"),
)

ONE_OFF_HOUSE = frozenset({"Y", "YES", "ONE", "SINGLE HOUSE"})


def _norm(text: str | None) -> str:
    return re.sub(r"\s+", " ", (text or "").upper()).strip()


def _first(rules: tuple[tuple[str, str], ...], text: str) -> str | None:
    return next((cls for cls, pattern in rules if re.search(pattern, text)), None)


def classify(
    decision: str | None, status: str | None, decided: object, withdrawn: object
) -> tuple[str, bool]:
    """Return (class, recognised). Unrecognised wording is "other", never a guess."""
    if withdrawn:
        return "withdrawn", True
    text = _norm(decision)
    if text and text not in ("N/A", "NA"):
        cls = _first(DECISION_RULES, text)
        return (cls, True) if cls else ("other", False)
    cls = _first(STATUS_RULES, _norm(status))
    if cls:
        return cls, True
    return ("pending", True) if not decided else ("other", False)


def _date(ms: int | None) -> str | None:
    # ponytail: ArcGIS dates are read as UTC; the service stores midnight UTC.
    return datetime.fromtimestamp(ms / 1000, UTC).date().isoformat() if ms is not None else None


def _past(day: str | None, today: str) -> str | None:
    """A decision date in the future is a typing error in the source (one says 2075): drop it."""
    return day if day and day <= today else None


def is_residential(units: int | None, one_off_house: str | None) -> bool:
    """True when the application states new dwellings: units, or a one-off house."""
    return bool(units and units > 0) or _norm(one_off_house) in ONE_OFF_HOUSE


def transform(collection: dict) -> list[dict]:
    today = datetime.now(UTC).date().isoformat()
    rows = []
    for f in collection["features"]:
        p = f["properties"]
        authority = p["PlanningAuthority"].strip()
        cls, recognised = classify(
            p.get("Decision"), p.get("ApplicationStatus"), p.get("DecisionDate"), p.get("WithdrawnDate")
        )
        units = p.get("NumResidentialUnits")
        rows.append(
            {
                "authority": authority,
                "application_number": p["ApplicationNumber"].strip(),
                "received": _date(p["ReceivedDate"]),
                "decided": _past(_date(p.get("DecisionDate")), today),
                "decision": (p.get("Decision") or "").strip() or None,
                "decision_class": cls,
                "recognised": recognised,
                "county": AUTHORITY_COUNTY[authority],
                "units_stated": units,
                "residential": is_residential(units, p.get("OneOffHouse")),
                "geometry": json.dumps(f["geometry"]),
            }
        )
    return rows


def check(collection: dict) -> list[str]:
    """An authority the table does not know would get no county: reject the run."""
    seen = {(f["properties"].get("PlanningAuthority") or "").strip() for f in collection["features"]}
    unknown = sorted(seen - set(AUTHORITY_COUNTY) - {""})
    return [f"unknown planning authorities: {', '.join(unknown)}"] if unknown else []


SOURCE = Source(
    name="planning",
    layer_url=LAYER,
    out_fields=(
        "PlanningAuthority",
        "ApplicationNumber",
        "ReceivedDate",
        "DecisionDate",
        "WithdrawnDate",
        "Decision",
        "ApplicationStatus",
        "NumResidentialUnits",
        "OneOffHouse",
    ),
    order_by="OBJECTID",
    required_fields=("PlanningAuthority", "ApplicationNumber", "ReceivedDate"),
    min_rows=200_000,
    table="planning_application",
    attribution=(
        "National Planning Applications, Department of Housing, Local Government and Heritage. CC BY 4.0."
    ),
    transform=transform,
    where=f"ReceivedDate >= DATE '{SINCE}'",
    check=check,
    after=("settlements",),
)
