# arvis/stability/stability_state_projector.py

from __future__ import annotations

from arvis.math.core.normalization import budget_ratio01, clamp01
from arvis.math.lyapunov.lyapunov import LyapunovState
from arvis.math.state.lyapunov_projection_state import (
    LyapunovProjectionState,
)


class StabilityStateProjector:
    """
    Extracts normalized stability signals from bundle.

    IMPORTANT:
    - must rely on existing bundle fields (ZKCS-safe)
    - must remain stable even if fields missing
    """

    @staticmethod
    def from_projection(state: LyapunovProjectionState) -> LyapunovState:
        # -------------------------
        # 1) Budget used
        # -------------------------
        budget_used = 0.0
        try:
            stab = getattr(state, "stability", None)
            if isinstance(stab, dict):
                cur = float(stab.get("current_changes", 0.0))
                mx = float(stab.get("max_changes", 0.0))
                budget_used = budget_ratio01(cur, mx)
        except (TypeError, ValueError, OverflowError):
            budget_used = 0.0

        # -------------------------
        # 2) Risk proxy (conflicts)
        # -------------------------
        try:
            risk = clamp01(float(state.collapse_risk))
        except (AttributeError, TypeError, ValueError, OverflowError):
            risk = 0.0

        # -------------------------
        # 3) Uncertainty proxy (frames)
        # -------------------------
        try:
            uncertainty = clamp01(1.0 - float(state.confidence))
        except (AttributeError, TypeError, ValueError, OverflowError):
            uncertainty = 0.0

        # -------------------------
        # 4) Governance proxy (gaps)
        # -------------------------
        try:
            governance = clamp01(float(state.drift_score))
        except (AttributeError, TypeError, ValueError, OverflowError):
            governance = 0.0

        return LyapunovState(
            budget_used=budget_used,
            risk=risk,
            uncertainty=uncertainty,
            governance=governance,
        )

    # -----------------------------------------------------
    # Snapshot projection (API / pipeline contract)
    # -----------------------------------------------------

    def project(self, snapshot: object) -> object:
        """
        Project a StabilitySnapshot into a usable representation.

        For now:
        - acts as identity (pass-through)
        - keeps compatibility with existing pipeline/tests

        Future:
        - normalization
        - smoothing
        - multi-horizon projection
        """

        return snapshot


# backward compatibility
LyapunovStateBuilder = StabilityStateProjector
