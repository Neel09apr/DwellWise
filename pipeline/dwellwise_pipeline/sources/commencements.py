"""Commencement notices: homes whose construction has started. CC BY 4.0.

National Building Control Office, "Building Commencement and Completion Data
2014 - Present", one CSV refreshed every morning. It has a row per building, so
one notice (a phase of a scheme) spans several rows; this source keeps one row
per residential notice received since ``SINCE``.

Privacy: the file carries street, Eircode, building and project names, which for
a one-off house identify a home. Only the fields below are kept, and a project
name only when the notice is for at least ``NAMED_FROM`` homes. Coordinates are
kept to place a notice in its town; the API never publishes them for small ones.
"""

from __future__ import annotations

import csv
import io
import json
import urllib.request
from collections.abc import Iterable
from datetime import UTC, datetime

from ..arcgis import USER_AGENT, FetchError
from .base import Source
from .planning import AUTHORITY_COUNTY

URL = (
    "https://data.nbco.gov.ie/dataset/2704a333-874d-46f5-b3bc-3673766bf816/resource/"
    "0774e781-7af8-46da-b623-872e74cf541e/download/buildingscnscccs.csv"
)
SINCE = "2020-01-01"  # same window as planning applications
NAMED_FROM = 5  # homes in a notice before its project name is shown

# Councils this file names differently from the planning dataset.
COUNTY = {
    **AUTHORITY_COUNTY,
    "Dún-Laoghaire Rathdown County Council": "DUBLIN",
    "Limerick City and County Council": "LIMERICK",
}


def _int(text: str) -> int | None:
    try:
        return int(float(text))
    except ValueError:
        return None


def _date(text: str) -> str | None:
    return text[:10] or None


def parse(lines: Iterable[str]) -> dict:
    """CSV lines to a GeoJSON-like collection, one feature per residential notice."""
    notices: dict[str, dict] = {}
    completed: dict[str, dict[str, int]] = {}  # notice -> completion certificate -> homes
    no_location = 0
    for row in csv.DictReader(lines):
        submitted = _date(row["CN_Date_Submitted_or_Received"])
        if "residential" not in row["CN_Proposed_use_of_building"] or not submitted or submitted < SINCE:
            continue
        number = row["CN_Number"].strip()
        if not number:
            continue  # one row in the file has no notice number: nothing to key it on
        if row["CCC_Number"]:
            completed.setdefault(number, {})[row["CCC_Number"]] = _int(row["CCC_Units_Completed"]) or 0
        if number in notices:
            continue
        lat, lng = row["CN_LAT"], row["CN_LNG"]
        if not lat or not lng:
            no_location += 1
            continue
        homes = _int(row["CN_Units_for_phase"])
        notices[number] = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [float(lng), float(lat)]},
            "properties": {
                "notice_number": number,
                "local_authority": row["LocalAuthority"].strip(),
                "submitted": submitted,
                "commenced": _date(row["CN_Commencement_Date"]),
                "expected_end": _date(row["CN_Proposed_end_date"]),
                "homes": homes,
                "scheme_homes": _int(row["CN_Total_Number_of_Dwelling_Units"]),
                "planning_ref": row["CN_Planning_Permission_Number"].strip() or None,
                "project_name": (
                    row["CN_Project_Name"].strip() or None if (homes or 0) >= NAMED_FROM else None
                ),
            },
        }
    for number, feature in notices.items():
        feature["properties"]["homes_completed"] = sum(completed.get(number, {}).values())
    return {"type": "FeatureCollection", "features": list(notices.values()), "no_location": no_location}


def fetch(url: str, *_args) -> dict:
    """Stream the 280 MB file, keeping only what ``parse`` keeps."""
    if not url.startswith("https://"):
        raise FetchError(f"refusing a non-HTTPS URL: {url}")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})  # noqa: S310 - HTTPS checked
    with urllib.request.urlopen(request, timeout=300) as response:  # noqa: S310 - HTTPS checked above
        return parse(io.TextIOWrapper(response, encoding="utf-8", errors="replace", newline=""))


def transform(collection: dict) -> list[dict]:
    rows = []
    for f in collection["features"]:
        p = f["properties"]
        rows.append({**p, "county": COUNTY[p["local_authority"]], "geometry": json.dumps(f["geometry"])})
    return rows


def check(collection: dict) -> list[str]:
    """Unknown councils would get no county; dates outside the data's life are corrupt."""
    problems = []
    seen = {f["properties"]["local_authority"] for f in collection["features"]}
    unknown = sorted(seen - set(COUNTY))
    if unknown:
        problems.append(f"unknown local authorities: {', '.join(unknown)}")
    latest = f"{datetime.now(UTC).year + 3}-12-31"
    odd = sum(
        1
        for f in collection["features"]
        if not ("2014-01-01" <= (f["properties"]["commenced"] or "") <= latest)
    )
    if odd:
        problems.append(f"{odd} notices with a commencement date missing or outside 2014 to {latest}")
    return problems


SOURCE = Source(
    name="commencements",
    layer_url=URL,
    out_fields=(),
    order_by="",
    required_fields=("notice_number", "local_authority", "submitted"),
    min_rows=60_000,
    table="commencement",
    attribution="Building Commencement and Completion Data, National Building Control Office. CC BY 4.0.",
    transform=transform,
    check=check,
    fetch=fetch,
)
