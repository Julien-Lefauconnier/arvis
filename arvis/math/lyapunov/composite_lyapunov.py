# arvis/math/lyapunov/composite_lyapunov.py

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from arvis.math.state.symbolic_state import SymbolicState

from .lyapunov import LyapunovState, lyapunov_value
from .slow_state import SlowState
from .target_map import target_map


@dataclass(frozen=True)
class CompositeLyapunov:
    """
    Composite Lyapunov candidate:

        W(x, z) = V_fast(x) + λ || z - T(x) ||²

    where:
    - x is the fast cognitive state
    - z is the slow / reflexive latent state
    - T(x) is the hybrid target map induced by symbolic + fast state

    Honest bounds (audit M4, campaign MATH-A M4): V_fast is a clamped
    convex combination in [0, 1] and the mismatch term is bounded by
    the state geometry, so W is a BOUNDED score (roughly [0, 1 +
    lambda_mismatch * dim]), not an unbounded energy. Past component
    saturation, the fast part of delta_W is blind to further
    degradation; the monitor's PAC risk ceiling covers that regime.

    delta_W is the energy variation between two steps measured UNDER
    THE SAME target availability: when one side has a symbolic anchor
    and the other does not, the two W values belong to different
    energy functions and their difference means nothing, so delta_W
    reports None instead of a number (audit M5).
    """

    lambda_mismatch: float = 0.5
    gamma_z: float = 1.0

    def W(
        self,
        fast: LyapunovState,
        slow: SlowState | None,
        symbolic: SymbolicState | None = None,
        T_x: np.ndarray | None = None,
    ) -> float:
        v_fast = float(lyapunov_value(fast))
        # --------------------------------------------------
        # Fallback: no slow state → pure fast energy
        # --------------------------------------------------
        if slow is None:
            return v_fast

        if T_x is None:
            if symbolic is None:
                # Neutral fallback only when no symbolic anchor is available.
                # This preserves well-definedness of W without introducing
                # hidden causal dependencies.
                T_x = np.zeros_like(slow.as_vector(), dtype=float)
            else:
                T_x = target_map(symbolic, fast=fast)

        z = slow.as_vector()
        e = z - T_x

        mismatch = float(np.dot(e, e))

        return v_fast + self.lambda_mismatch * mismatch

    def delta_W(
        self,
        fast_prev: LyapunovState,
        fast_next: LyapunovState,
        slow_prev: SlowState | None,
        slow_next: SlowState | None,
        symbolic_prev: SymbolicState | None = None,
        symbolic_next: SymbolicState | None = None,
    ) -> float | None:
        # -----------------------------------------
        # FAST-ONLY fallback
        # -----------------------------------------
        if slow_prev is None or slow_next is None:
            v_prev = float(lyapunov_value(fast_prev))
            v_next = float(lyapunov_value(fast_next))
            return v_next - v_prev

        # A delta compares two evaluations of the SAME energy. When the
        # symbolic anchor exists on one side only, W_prev and W_next use
        # different target maps and their difference is not an energy
        # variation: its sign could flip on the anchor's appearance
        # alone, and that sign feeds recovery detection (audit M5).
        if (symbolic_prev is None) != (symbolic_next is None):
            return None

        T_prev = (
            target_map(symbolic_prev, fast=fast_prev)
            if symbolic_prev is not None
            else np.zeros_like(slow_prev.as_vector(), dtype=float)
        )
        T_next = (
            target_map(symbolic_next, fast=fast_next)
            if symbolic_next is not None
            else np.zeros_like(slow_next.as_vector(), dtype=float)
        )

        # True energy variation
        w_prev = float(
            self.W(
                fast=fast_prev,
                slow=slow_prev,
                symbolic=symbolic_prev,
                T_x=T_prev,
            )
        )
        w_next = float(
            self.W(
                fast=fast_next,
                slow=slow_next,
                symbolic=symbolic_next,
                T_x=T_next,
            )
        )
        return w_next - w_prev

    def check_small_gain(
        self,
        eta: float,
        alpha: float,
        L_T: float,
    ) -> bool:
        """Small-gain check kappa_eff = alpha - gamma_z * eta * L_T > 0.

        alpha (the decrease rate of A6) and L_T (the target-map
        Lipschitz constant of A7) are NOT measured at runtime: the
        caller must supply the values it assumes or estimated, and owns
        that assumption. The old defaults (0.3, 1.0) made the check
        pass by construction (audit M6).
        """
        kappa_eff = float(alpha) - self.gamma_z * float(eta) * float(L_T)
        return kappa_eff > 1e-6
