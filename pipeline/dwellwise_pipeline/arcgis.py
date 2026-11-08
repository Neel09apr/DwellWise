"""Read every feature from an ArcGIS feature layer as GeoJSON, page by page.

ArcGIS answers some failures with HTTP 200 and a JSON body that is not data:
an error object, or "file is being generated, check back later". Anything
without a features list is treated as a failure and retried, and is never
passed on to be stored as a snapshot.
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from collections.abc import Callable

USER_AGENT = "dwellwise-pipeline (+https://github.com/Neel09apr/DwellWise)"
PAGE_SIZE = 1000
RETRIES = 3

Opener = Callable[[str], bytes]


class FetchError(RuntimeError):
    """The service did not return usable features."""


def http_get(url: str, timeout: float = 60) -> bytes:
    if not url.startswith("https://"):
        raise FetchError(f"refusing a non-HTTPS URL: {url}")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})  # noqa: S310 - HTTPS checked
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - HTTPS checked above
        return response.read()


def _get_features_page(url: str, opener: Opener, sleep: Callable[[float], None]) -> dict:
    last: Exception | None = None
    for attempt in range(RETRIES):
        try:
            body = json.loads(opener(url))
            if isinstance(body, dict) and isinstance(body.get("features"), list):
                return body
            last = FetchError(f"no features in the response: {str(body)[:200]}")
        except (OSError, ValueError) as exc:  # network failures and malformed JSON
            last = exc
        if attempt < RETRIES - 1:
            sleep(2**attempt)
    raise FetchError(f"{url} failed after {RETRIES} attempts: {last}") from last


def fetch_features(
    layer_url: str,
    out_fields: list[str],
    order_by: str,
    *,
    opener: Opener = http_get,
    sleep: Callable[[float], None] = time.sleep,
    page_size: int = PAGE_SIZE,
) -> dict:
    """Return every feature of the layer as one GeoJSON FeatureCollection in WGS84."""
    features: list[dict] = []
    offset = 0
    while True:
        query = urllib.parse.urlencode(
            {
                "where": "1=1",
                "outFields": ",".join(out_fields),
                "returnGeometry": "true",
                "outSR": "4326",
                "orderByFields": order_by,  # paging is only stable with a fixed order
                "resultOffset": offset,
                "resultRecordCount": page_size,
                "f": "geojson",
            }
        )
        page = _get_features_page(f"{layer_url}/query?{query}", opener, sleep)
        batch = page["features"]
        features.extend(batch)
        more = page.get("exceededTransferLimit") or (page.get("properties") or {}).get(
            "exceededTransferLimit"
        )
        if not more or not batch:
            return {"type": "FeatureCollection", "features": features}
        offset += len(batch)
