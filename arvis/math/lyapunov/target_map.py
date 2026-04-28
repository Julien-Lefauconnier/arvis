# arvis/math/lyapunov/target_map.py

from __future__ import annotations

import numpy as np

from arvis.cognition.observability.symbolic.symbolic_state import SymbolicState
from arvis.math.lyapunov.lyapunov import LyapunovState


def _fast_vector(fast: LyapunovState) -> np.ndarray:
    return np.array(
        [
            float(fast.budget_used),
            float(fast.risk),
            float(fast.uncertainty),
            float(fast.governance),
        ],
        dtype=float,
    )


def target_map(
    state: SymbolicState,
    fast: LyapunovState | None = None,
    rho_fast: float = 0.30,
) -> np.ndarray:
    """
    T(x) : target map from symbolic/fast state to slow geometry.

    The target is hybrid:
    - a symbolic anchor built from causal observable quantities
    - optionally coupled to the fast Lyapunov state

    This avoids a static target when the fast dynamics evolve,
    which is necessary for a meaningful composite Lyapunov energy.
    """

    confidence = float(state.intent_confidence)
    conflict = float(state.conflict_severity)
    override = float(state.override_rate)

    stability_proxy = confidence * (1.0 - conflict)

    symbolic_target = np.array(
        [
            confidence,  # attractivity
            1.0 - conflict,  # coherence
            override,  # instability injection
            stability_proxy,  # symbolic stability proxy
        ],
        dtype=float,
    )

    if fast is None:
        return symbolic_target

    rho = float(max(0.0, min(1.0, rho_fast)))
    fast_target = _fast_vector(fast)

    # Hybrid target:
    # T = (1-rho) * T_symbolic + rho * T_fast
    return (1.0 - rho) * symbolic_target + rho * fast_target
