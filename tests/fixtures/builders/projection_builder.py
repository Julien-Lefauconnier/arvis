# tests/fixtures/builders/projection_builder.py

from __future__ import annotations

from arvis.math.state.lyapunov_projection_state import (
    LyapunovProjectionState,
)


def build_projection_state(
    *,
    conflict_pressure: float = 0.2,
    drift_score: float = 0.1,
    collapse_risk: float = 0.3,
    confidence: float = 0.8,
) -> LyapunovProjectionState:
    return LyapunovProjectionState(
        conflict_pressure=conflict_pressure,
        drift_score=drift_score,
        collapse_risk=collapse_risk,
        confidence=confidence,
    )
