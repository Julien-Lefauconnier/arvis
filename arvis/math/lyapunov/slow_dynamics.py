# arvis/math/lyapunov/slow_dynamics.py

from __future__ import annotations

from arvis.math.lyapunov.slow_state import SlowState
from typing import Iterable

def update_slow_state(
    z_prev: SlowState,
    T_x: Iterable[float],
    eta: float = 0.05,
) -> SlowState:
    prev = z_prev.as_vector()
    new = [(1.0 - eta) * p + eta * t for p, t in zip(prev, T_x)]
    return SlowState(*new)