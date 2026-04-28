# arvis/stability/predictive_snapshot.py

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PredictiveSnapshot:
    predicted_v: float
    slope: float
    time_to_critical: Optional[float]
    verdict: Optional[str]
    horizon: Optional[int] = None
