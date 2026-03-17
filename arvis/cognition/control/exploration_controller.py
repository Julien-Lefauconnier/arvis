# arvis/cognition/control/exploration_controller.py

from __future__ import annotations

from arvis.cognition.control.exploration_snapshot import ExplorationSnapshot
from arvis.math.signals import RiskSignal, DriftSignal
from arvis.math.signals.utils import signal_value


class ExplorationController:
    """
    Kernel-safe exploration/exploitation policy.
    """

    def compute(
        self,
        *,
        regime: str | None,
        collapse_risk: float | None,
        drift_score: float | None,
        stable: bool | None,
    ) -> ExplorationSnapshot:
        
        # -----------------------------------------
        # Signal-safe normalization (boundary)
        # -----------------------------------------
        cr = collapse_risk
        ds = drift_score

        cr_val = signal_value(cr, 0.0)
        ds_val = signal_value(ds, 0.0)

        r = (regime or "neutral").lower()
        cr = float(collapse_risk) if collapse_risk is not None else 0.0
        ds = float(drift_score) if drift_score is not None else 0.0
        st = bool(stable) if stable is not None else True

        exploration = 1.0
        confirm = 1.0
        abstain = 1.0
        budget = 1.0
        why = ["base"]

        if r == "stable":
            exploration *= 1.2
            confirm *= 0.9
            budget *= 1.1
            why.append("regime=stable")

        elif r == "oscillatory":
            why.append("regime=oscillatory")

        elif r == "critical":
            exploration *= 0.8
            confirm *= 1.2
            budget *= 0.8
            why.append("regime=critical")

        elif r == "chaotic":
            exploration *= 0.5
            confirm *= 1.5
            abstain *= 1.3
            budget *= 0.6
            why.append("regime=chaotic")

        if hasattr(cr, "is_critical") and cr.is_critical():
            exploration *= 0.6
            confirm *= 1.3
            abstain *= 1.2
            budget *= 0.7
            why.append("collapse>=0.8")

        elif cr_val >= 0.5:
            exploration *= 0.85
            confirm *= 1.1
            budget *= 0.85
            why.append("collapse>=0.5")

        if hasattr(ds, "is_high") and ds.is_high():
            confirm *= 1.2
            budget *= 0.85
            why.append("drift>=0.7")

        if not st:
            exploration *= 0.8
            confirm *= 1.2
            budget *= 0.7
            why.append("unstable")

        exploration = max(0.3, min(exploration, 1.5))
        confirm = max(0.7, min(confirm, 2.0))
        abstain = max(0.8, min(abstain, 2.0))
        budget = max(0.5, min(budget, 1.3))

        return ExplorationSnapshot(
            exploration_factor=exploration,
            confirmation_bias=confirm,
            abstain_bias=abstain,
            change_budget_scale=budget,
            rationale="|".join(why),
        )