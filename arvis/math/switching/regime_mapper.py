# arvis/math/switching/regime_mapper.py

from __future__ import annotations

from arvis.math.switching.regime_state import RegimeState, TheoreticalRegime


def map_regime(name: str | None, confidence: float = 0.0) -> RegimeState:
    raw = str(name or "transition").lower()

    if raw == "stable":
        q = TheoreticalRegime.STABLE
    elif raw == "oscillatory":
        q = TheoreticalRegime.OSCILLATORY
    elif raw == "critical":
        q = TheoreticalRegime.CRITICAL
    elif raw == "chaotic":
        q = TheoreticalRegime.CHAOTIC
    elif raw == "neutral":
        q = TheoreticalRegime.NEUTRAL
    else:
        q = TheoreticalRegime.TRANSITION

    return RegimeState(q_t=q, confidence=float(confidence or 0.0))
