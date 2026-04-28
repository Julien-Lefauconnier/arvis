# arvis/stability/stability_state_projector.py

from __future__ import annotations

from arvis.cognition.bundle.cognitive_bundle_snapshot import CognitiveBundleSnapshot
from arvis.math.core.normalization import budget_ratio01, clamp01
from arvis.math.lyapunov.lyapunov import LyapunovState


class StabilityStateProjector:
    """
    Extracts normalized stability signals from bundle.

    IMPORTANT:
    - must rely on existing bundle fields (ZKCS-safe)
    - must remain stable even if fields missing
    """

    @staticmethod
    def from_bundle(bundle: CognitiveBundleSnapshot) -> LyapunovState:
        # -------------------------
        # 1) Budget used
        # -------------------------
        budget_used = 0.0
        try:
            stab = getattr(bundle.explanation, "stability", None)
            if isinstance(stab, dict):
                cur = float(stab.get("current_changes", 0.0))
                mx = float(stab.get("max_changes", 0.0))
                budget_used = budget_ratio01(cur, mx)
        except Exception:
            budget_used = 0.0

        # -------------------------
        # 2) Risk proxy (conflicts)
        # -------------------------
        try:
            conflicts = getattr(bundle.decision_result, "conflicts", []) or []
            # scale: 0 conflict => 0, >=5 => 1
            risk = clamp01(len(conflicts) / 5.0)
        except Exception:
            risk = 0.0

        # -------------------------
        # 3) Uncertainty proxy (frames)
        # -------------------------
        try:
            frames = getattr(bundle.decision_result, "uncertainty_frames", []) or []
            # scale: 0 frame => 0, >=5 => 1
            uncertainty = clamp01(len(frames) / 5.0)
        except Exception:
            uncertainty = 0.0

        # -------------------------
        # 4) Governance proxy (gaps)
        # -------------------------
        try:
            gaps = getattr(bundle.decision_result, "gaps", []) or []
            governance = clamp01(len(gaps) / 5.0)
        except Exception:
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
