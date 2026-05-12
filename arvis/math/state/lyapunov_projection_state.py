# arvis/math/state/lyapunov_projection_state.py

from dataclasses import dataclass


@dataclass(frozen=True)
class LyapunovProjectionState:
    conflict_pressure: float
    drift_score: float
    collapse_risk: float
    confidence: float
