# arvis/math/lyapunov/composite_lyapunov.py

from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from .lyapunov import LyapunovState, lyapunov_value
from .slow_state import SlowState
from .target_map import target_map
from arvis.cognition.observability.symbolic.symbolic_state import SymbolicState


@dataclass(frozen=True)
class CompositeLyapunov:
    """
    Composite Lyapunov candidate:

        W(x, z) = V_fast(x) + λ || z - T(x) ||²

    where:
    - x is the fast cognitive state
    - z is the slow / reflexive latent state
    - T(x) is the hybrid target map induced by symbolic + fast state

    Important:
    - no clamping: W is a genuine energy, not a bounded score
    - delta_W is the true energy variation between two time steps
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
    ) -> float:
        # -----------------------------------------
        # FAST-ONLY fallback
        # -----------------------------------------
        if slow_prev is None or slow_next is None:
            v_prev = float(lyapunov_value(fast_prev))
            v_next = float(lyapunov_value(fast_next))
            return v_next - v_prev

        def _zero_target(slow: SlowState | None) -> np.ndarray:
            """
            Safe fallback when no symbolic anchor AND slow state is missing.
            Ensures delta_W remains well-defined.
            """
            if slow is not None:
                return np.zeros_like(slow.as_vector(), dtype=float)
            return np.zeros(1, dtype=float)

        T_prev = (
            target_map(symbolic_prev, fast=fast_prev)
            if symbolic_prev is not None
            else _zero_target(slow_prev)
        )
        T_next = (
            target_map(symbolic_next, fast=fast_next)
            if symbolic_next is not None
            else _zero_target(slow_next)
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
        eta: float = 0.05,
        alpha: float = 0.3,
        L_T: float = 1.0,
    ) -> bool:
        kappa_eff = float(alpha) - self.gamma_z * float(eta) * float(L_T)
        return kappa_eff > 1e-6
