# arvis/stability/predictive_snapshot.py

from dataclasses import dataclass


@dataclass(frozen=True)
class PredictiveSnapshot:
    predicted_v: float
    slope: float
    time_to_critical: float | None
    verdict: str | None
    horizon: int | None = None
