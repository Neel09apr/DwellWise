"""Name normalisation for joins between sources that spell places differently."""

import re
import unicodedata


def name_key(name: str) -> str:
    """Fold fadas and drop everything but a-z: 'Béal an Mhuirthead' -> 'bealanmhuirthead'."""
    folded = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z]", "", folded.lower())
