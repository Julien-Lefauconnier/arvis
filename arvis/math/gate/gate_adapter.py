# arvis/math/gate/gate_adapter.py

from typing import Any

from arvis.math.lyapunov.lyapunov import LyapunovState


def ensure_lyapunov_state(value: Any) -> LyapunovState:
    if isinstance(value, LyapunovState):
        return value
    if isinstance(value, (float, int)):
        return LyapunovState.from_scalar(float(value))
    return LyapunovState.from_scalar(0.0)
