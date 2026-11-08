import importlib.util
from pathlib import Path

from dwellwise_api.names import name_key

EXAMPLES = {
    "Béal an Mhuirthead": "bealanmhuirthead",
    "Carrick-On-Shannon": "carrickonshannon",
    "Carrick on Shannon": "carrickonshannon",
    "  CORK City & Suburbs ": "corkcitysuburbs",
}


def test_the_api_folds_names_like_the_pipeline():
    pipeline_names = Path(__file__).resolve().parents[3] / "pipeline" / "dwellwise_pipeline" / "names.py"
    spec = importlib.util.spec_from_file_location("pipeline_names", pipeline_names)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for raw, key in EXAMPLES.items():
        assert name_key(raw) == key
        assert module.name_key(raw) == key
