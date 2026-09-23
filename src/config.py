"""Configuration helpers: load params.yaml into plain dictionaries.

Keeps training code free of hardcoded values and lets DVC detect
parameter changes (a changed params.yaml value triggers pipeline re-runs).
"""

from functools import lru_cache
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PARAMS_PATH = PROJECT_ROOT / "params.yaml"


@lru_cache
def load_params(path: Path = PARAMS_PATH) -> dict:
    """Load and cache params.yaml as a nested dict."""
    with open(path) as f:
        return yaml.safe_load(f)