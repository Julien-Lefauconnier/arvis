# compliance/scenarios/loader.py

import yaml
from pathlib import Path


def load_scenario(name: str):
    base = Path(__file__).parent
    path = base / f"{name}.yaml"

    with open(path, "r") as f:
        return yaml.safe_load(f)
