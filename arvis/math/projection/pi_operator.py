# arvis/math/projection/pi_operator.py

from __future__ import annotations

from typing import Any


class PiOperator:
    """
    Projection operator Π:
    Projects a state into a safe / stable domain.
    """

    def project(self, state: dict[str, float], ctx: Any = None) -> dict[str, float]:
        if state is None:
            return {}

        projected = {}

        # -----------------------------------------
        # Context-aware parameters
        # -----------------------------------------
        regime = getattr(getattr(ctx, "adaptive_snapshot", None), "regime", "stable")
        validity = getattr(getattr(ctx, "validity_envelope", None), "valid", True)

        # Projection strength
        if not validity:
            alpha = 0.5  # aggressive projection
        elif regime == "critical":
            alpha = 0.7  # moderate
        else:
            alpha = 1.0  # light (almost identity)

        # -----------------------------------------
        # Stability feedback control
        # -----------------------------------------
        delta_v = getattr(ctx, "_dv", 0.0) if ctx is not None else 0.0
        try:
            dv = float(delta_v)
        except Exception:
            dv = 0.0

        # If system diverges → increase contraction
        if dv > 0.0:
            alpha = min(alpha, 0.6)

        # If strongly diverging → strong contraction
        if dv > 0.2:
            alpha = min(alpha, 0.2)

        for k, v in state.items():
            # -----------------------------------------
            # Ignore non-numeric values (strict contract)
            # -----------------------------------------
            if not isinstance(v, (int, float)) or v != v:
                continue

            v = float(v)

            # -----------------------------------------
            # Smooth projection instead of hard clip
            # -----------------------------------------
            v_proj = v / (1.0 + abs(v))

            # -----------------------------------------
            # Adaptive blending:
            # keep a share of original value, contract the rest
            # -----------------------------------------
            blended = alpha * v + (1.0 - alpha) * v_proj

            # -----------------------------------------
            # FINAL SAFETY PROJECTION (kernel invariant)
            # -----------------------------------------
            projected[k] = blended / (1.0 + abs(blended))

        return projected
