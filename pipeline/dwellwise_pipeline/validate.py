"""Checks every collection must pass before it may touch the database."""

from __future__ import annotations

import re

from .sources.base import Source

# Planning data must never carry who applied or where they live. Field names
# are compared with case, spaces and punctuation removed.
FORBIDDEN_FIELDS = frozenset({"applicant", "applicantname", "applicantaddress", "agentname", "agentaddress"})


class ValidationError(ValueError):
    """The collection is not safe to load."""


def _norm(field: str) -> str:
    return re.sub(r"[^a-z]", "", field.lower())


def validate(source: Source, collection: dict, previous_rows: int | None, max_drift: float = 0.2) -> None:
    features = collection["features"]
    count = len(features)
    problems: list[str] = []

    if count < source.min_rows:
        problems.append(f"{count} rows, expected at least {source.min_rows}")
    if previous_rows and abs(count - previous_rows) > max_drift * previous_rows:
        problems.append(f"{count} rows against {previous_rows} last time (more than {max_drift:.0%} change)")

    fields = {key for feature in features for key in (feature.get("properties") or {})}
    forbidden = sorted(f for f in fields if _norm(f) in FORBIDDEN_FIELDS)
    if forbidden:
        problems.append(f"personal-data fields present: {', '.join(forbidden)}")

    for field in source.required_fields:
        missing = sum(1 for f in features if (f.get("properties") or {}).get(field) in (None, ""))
        if missing:
            problems.append(f"{missing} rows missing {field}")

    no_geometry = sum(1 for f in features if not f.get("geometry"))
    if no_geometry:
        problems.append(f"{no_geometry} rows without geometry")

    if problems:
        raise ValidationError(f"{source.name}: " + "; ".join(problems))
