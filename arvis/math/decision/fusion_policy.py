# arvis/math/decision/fusion_policy.py

from __future__ import annotations
from typing import Optional

from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


def fusion_policy(
    fast_verdict: LyapunovVerdict,
    delta_w: Optional[float],
    switching_safe: bool,
    use_composite: bool = True,
) -> LyapunovVerdict:
    """
    Formal fusion policy (paper-aligned):

    Priority order:
    1. Hard safety (ABSTAIN)
    2. Composite Lyapunov (ΔW)
    3. Fast Lyapunov gate
    4. Switching constraint (non-blocking)

    Design:
    - Composite is directional (energy-based)
    - Fast gate is local stability
    - Switching is global constraint (non overriding)
    """

    # -----------------------------------------
    # 1. Hard safety
    # -----------------------------------------
    if fast_verdict == LyapunovVerdict.ABSTAIN:
        return LyapunovVerdict.ABSTAIN

    # -----------------------------------------
    # 2. Composite Lyapunov (paper core)
    # -----------------------------------------
    if use_composite and delta_w is not None:
        if delta_w > 1e-6:
            return LyapunovVerdict.REQUIRE_CONFIRMATION
        elif delta_w < -1e-6:
            return LyapunovVerdict.ALLOW

    # -----------------------------------------
    # 3. Fast Lyapunov (fallback)
    # -----------------------------------------
    return fast_verdict