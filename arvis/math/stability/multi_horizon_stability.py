# arvis/math/stability/multi_horizon_stability.py

from dataclasses import dataclass


@dataclass
class MultiHorizonSnapshot:
    collapse_risk: float
    stability_confidence: float
    early_warning: bool
    mode_hint: str


class MultiHorizonStabilityObserver:
    """
    Fusion of:
    - Lyapunov (instant stability)
    - Trajectory (empirical drift)
    - Predictive (future risk)

    Passive scientific observer.
    """

    def evaluate(
        self,
        *,
        lyapunov_v: float,
        trajectory_vmax: float,
        predictive_ttc: int | None,
    ) -> MultiHorizonSnapshot:
        # -------------------------
        # Collapse risk
        # -------------------------
        risk = max(
            lyapunov_v,
            trajectory_vmax,
        )

        if predictive_ttc is not None:
            risk = max(risk, 1.0 / (1 + predictive_ttc))

        risk = min(1.0, risk)

        # -------------------------
        # Confidence
        # -------------------------
        confidence = 1.0 - risk

        # -------------------------
        # Early warning
        # -------------------------
        early_warning = False

        if predictive_ttc is not None and predictive_ttc < 5:
            early_warning = True

        if trajectory_vmax > 0.7:
            early_warning = True

        # -------------------------
        # Mode hint (future adaptive cognition)
        # -------------------------
        if risk > 0.8:
            mode = "SAFE"
        elif risk > 0.5:
            mode = "CAUTION"
        else:
            mode = "NORMAL"

        return MultiHorizonSnapshot(
            collapse_risk=risk,
            stability_confidence=confidence,
            early_warning=early_warning,
            mode_hint=mode,
        )
