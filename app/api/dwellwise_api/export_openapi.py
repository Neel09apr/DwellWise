"""Write openapi.json next to the package; CI fails if it is out of date."""

import json
from pathlib import Path

from .config import Settings
from .main import create_app

if __name__ == "__main__":
    schema = create_app(Settings()).openapi()
    out = Path(__file__).resolve().parent.parent / "openapi.json"
    out.write_text(json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out}")  # noqa: T201
