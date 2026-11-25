"""CSO sale prices of homes, by Eircode routing area and by county or council area. CC BY 4.0.

Two tables from the CSO's PxStat API, both built from Revenue stamp duty filings
of market purchases by households: HPM04 by Eircode routing key (139 areas) and
HPM05 by region, county and council area. Monthly, by the month the deed was
executed, for all homes and for new homes. The CSO leaves small counts empty
(suppressed); they stay null and are never filled in. These are area figures:
they say what homes in an area sold for, never what a site is worth.
"""

from __future__ import annotations

import itertools
import json
import urllib.request
from datetime import UTC, datetime

from ..arcgis import USER_AGENT, FetchError
from .base import Source

API = "https://ws.cso.ie/public/api.jsonrpc"
SINCE = "202001"  # months before this are not kept
STATUS = {"-": "all", "01": "new"}
MEASURES = {"C01": "sales", "C03": "mean", "C04": "median"}  # C02 is total value: not used

TABLES = {
    "HPM04": {
        "kind": "eircode",
        "area": "C03349V04063",
        "fixed": {"C03341V04028": "02", "C03344V04031": "-"},  # deeds executed; every buyer type
        "skip": {"-"},  # its "All" row repeats HPM05's
    },
    "HPM05": {
        "kind": "region",
        "area": "C03348V04035",
        "fixed": {"C03341V04028": "02", "C03347V04034": "-"},  # deeds executed; every dwelling type
        "skip": set(),
    },
}
STATUS_DIM = "C03346V04033"


def query(table: str) -> dict:
    spec = TABLES[table]
    dimension = {
        "STATISTIC": {"category": {"index": [f"{table}{m}" for m in MEASURES]}},
        STATUS_DIM: {"category": {"index": list(STATUS)}},
        **{dim: {"category": {"index": [code]}} for dim, code in spec["fixed"].items()},
    }
    return {
        "jsonrpc": "2.0",
        "method": "PxStat.Data.Cube_API.ReadDataset",
        "params": {
            "class": "query",
            "id": list(dimension),
            "dimension": dimension,
            "extension": {
                "pivot": None,
                "codes": False,
                "language": {"code": "en"},
                "format": {"type": "JSON-stat", "version": "2.0"},
                "matrix": table,
            },
            "version": "2.0",
        },
    }


def parse(table: str, cube: dict) -> list[dict]:
    """A JSON-stat cube to one feature per area, month and status. Values are row-major."""
    spec = TABLES[table]
    dims = cube["id"]
    categories = [list(cube["dimension"][d]["category"]["index"]) for d in dims]
    labels = cube["dimension"][spec["area"]]["category"]["label"]
    values = cube["value"]
    rows: dict[tuple[str, str, str], dict] = {}
    for flat, combo in enumerate(itertools.product(*categories)):
        at = dict(zip(dims, combo, strict=True))
        month, area = at["TLIST(M1)"], at[spec["area"]]
        if month < SINCE or area in spec["skip"]:
            continue
        key = (area, month, STATUS[at[STATUS_DIM]])
        row = rows.setdefault(
            key,
            {
                "kind": spec["kind"],
                "code": area,
                "name": labels[area].split(": ", 1)[-1],
                "month": f"{month[:4]}-{month[4:]}-01",
                "status": key[2],
                "sales": None,
                "median": None,
                "mean": None,
            },
        )
        value = values[flat]
        row[MEASURES[at["STATISTIC"][-3:]]] = None if value is None else round(value)
    return [
        {"type": "Feature", "geometry": None, "properties": r}
        for r in rows.values()
        if any(r[m] is not None for m in MEASURES.values())
    ]


def http_post(url: str, body: dict) -> dict:
    if not url.startswith("https://"):
        raise FetchError(f"refusing a non-HTTPS URL: {url}")
    request = urllib.request.Request(  # noqa: S310 - HTTPS checked above
        url,
        data=json.dumps(body).encode(),
        headers={"User-Agent": USER_AGENT, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:  # noqa: S310 - HTTPS checked above
        answer = json.loads(response.read())
    if "result" not in answer:
        raise FetchError(f"PxStat answered without a result: {str(answer)[:200]}")
    return answer["result"]


def fetch(url: str, *_args, post=http_post) -> dict:
    features = [f for table in TABLES for f in parse(table, post(url, query(table)))]
    return {"type": "FeatureCollection", "features": features}


def transform(collection: dict) -> list[dict]:
    return [f["properties"] for f in collection["features"]]


def check(collection: dict) -> list[str]:
    """Every Eircode area present, the newest month recent, prices plausible."""
    props = [f["properties"] for f in collection["features"]]
    problems = []
    areas = {p["code"] for p in props if p["kind"] == "eircode"}
    if len(areas) < 130:
        problems.append(f"{len(areas)} Eircode areas, expected about 139")
    newest = max((p["month"] for p in props), default="")
    today = datetime.now(UTC).date()
    oldest_allowed = f"{today.year - (today.month <= 6)}-{(today.month - 7) % 12 + 1:02d}-01"  # 6 months back
    if newest < oldest_allowed:
        problems.append(f"newest month {newest or 'none'} is older than six months")
    odd = sum(1 for p in props if p["median"] is not None and not 10_000 <= p["median"] <= 5_000_000)
    if odd:
        problems.append(f"{odd} median prices outside 10,000 to 5,000,000 euro")
    return problems


SOURCE = Source(
    name="prices",
    layer_url=API,
    out_fields=(),
    order_by="",
    required_fields=("kind", "code", "name", "month", "status"),
    min_rows=20_000,
    table="price",
    attribution="Central Statistics Office, tables HPM04 and HPM05 (Revenue stamp duty data). CC BY 4.0.",
    transform=transform,
    check=check,
    fetch=fetch,
    geometry=False,
)
