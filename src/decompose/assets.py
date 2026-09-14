"""Locate TaskSpec-owned decomposition resources."""
from pathlib import Path
def assets_root() -> Path:
    return Path(__file__).resolve().parents[2]
