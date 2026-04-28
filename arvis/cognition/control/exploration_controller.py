# arvis/cognition/control/exploration_controller.py

from __future__ import annotations

from arvis.cognition.control.exploration_snapshot import ExplorationSnapshot
from arvis.math.signals import RiskSignal, DriftSignal


class ExplorationController:
    """
    Kernel-safe exploration/exploitation policy.
    """

    def compute(
        self,
        *,
        regime: str | None,
        collapse_risk: float | RiskSignal | None,
        drift_score: float | DriftSignal | None,
        stable: bool | None,
    ) -> ExplorationSnapshot:
        r = (regime or "neutral").lower()

        if isinstance(collapse_risk, RiskSignal):
            cr = float(collapse_risk)
            risk_is_critical = collapse_risk.is_critical()
        else:
            cr = float(collapse_risk or 0.0)
            risk_is_critical = cr >= 0.8

        if isinstance(drift_score, DriftSignal):
            ds = float(drift_score)
        else:
            ds = float(drift_score or 0.0)

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

        if risk_is_critical:
            exploration *= 0.6
            confirm *= 1.3
            abstain *= 1.2
            budget *= 0.7
            why.append("collapse>=0.8")

        elif cr >= 0.5:
            exploration *= 0.85
            confirm *= 1.1
            budget *= 0.85
            why.append("collapse>=0.5")

        if ds >= 0.7:
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
