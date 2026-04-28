# arvis/math/lyapunov/quadratic_projection.py

from __future__ import annotations

import numpy as np

from arvis.math.lyapunov.lyapunov import LyapunovState
from arvis.math.lyapunov.quadratic_lyapunov import QuadraticLyapunovState


def project_operational_to_quadratic(
    state: LyapunovState | None,
) -> QuadraticLyapunovState | None:
    """
    Projects current operational fast state into a paper-aligned x_t vector.
    """
    if state is None:
        return None

    x = np.array(
        [
            float(state.budget_used),
            float(state.risk),
            float(state.uncertainty),
            float(state.governance),
        ],
        dtype=float,
    )
    return QuadraticLyapunovState(x=x)
