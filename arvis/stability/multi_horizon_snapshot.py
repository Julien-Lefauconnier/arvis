# arvis/stability/multi_horizon_snapshot.py

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class MultiHorizonSnapshot:
    collapse_risk: float
    stability_confidence: float
    early_warning: bool
    mode_hint: Optional[str] = None