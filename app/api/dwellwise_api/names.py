"""Must match pipeline/dwellwise_pipeline/names.py: the pipeline writes name_key with it.

tests/test_names.py pins both to the same examples.
"""

import re
import unicodedata


def name_key(name: str) -> str:
    folded = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z]", "", folded.lower())
