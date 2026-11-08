from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class Source:
    name: str
    layer_url: str
    out_fields: tuple[str, ...]
    order_by: str
    required_fields: tuple[str, ...]
    min_rows: int
    table: str
    attribution: str
    transform: Callable[[dict], list[dict]]
