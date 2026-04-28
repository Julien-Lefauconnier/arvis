# arvis/math/state/fast_projection.py

from arvis.math.lyapunov.lyapunov import LyapunovState
from arvis.math.state.fast_state import FastCognitiveState


def project_fast_to_lyapunov(x: FastCognitiveState) -> LyapunovState:
    """
    Projection Π(x_t) → LyapunovState
    (placeholder for now)
    """
    # simple placeholder mapping
    vals = list(x.values) + [0.0] * 4
    return LyapunovState(
        budget_used=vals[0],
        risk=vals[1],
        uncertainty=vals[2],
        governance=vals[3],
    )
