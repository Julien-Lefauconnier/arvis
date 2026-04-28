# arvis/math/adaptive/adaptive_control_policy.py

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AdaptiveControlOutput:
    exploration_scale: float
    conservatism_scale: float
    risk_tolerance_scale: float
    regime: str


@dataclass(frozen=True)
class AdaptiveControlConfig:
    min_exploration: float = 0.2
    max_exploration: float = 1.0

    min_conservatism: float = 0.5
    max_conservatism: float = 2.0

    min_risk: float = 0.3
    max_risk: float = 1.0


class AdaptiveControlPolicy:
    def __init__(self, config: AdaptiveControlConfig | None = None) -> None:
        self.config = config or AdaptiveControlConfig()

    def compute(
        self,
        kappa_eff: float | None,
        margin: float | None,
        regime: str | None,
    ) -> AdaptiveControlOutput:
        # fallback safe
        if kappa_eff is None or margin is None or regime is None:
            return AdaptiveControlOutput(
                exploration_scale=0.5,
                conservatism_scale=1.5,
                risk_tolerance_scale=0.5,
                regime="fallback",
            )

        # -----------------------------
        # REGIME LOGIC
        # -----------------------------

        if regime == "unstable":
            return AdaptiveControlOutput(
                exploration_scale=self.config.min_exploration,
                conservatism_scale=self.config.max_conservatism,
                risk_tolerance_scale=self.config.min_risk,
                regime="unstable",
            )

        if regime == "marginal":
            return AdaptiveControlOutput(
                exploration_scale=0.4,
                conservatism_scale=1.7,
                risk_tolerance_scale=0.4,
                regime="marginal",
            )

        # stable regime
        # -----------------------------
        # continuous modulation
        # -----------------------------

        # kappa_eff ∈ [0,1)
        k = max(0.0, min(0.99, kappa_eff))

        exploration = self.config.min_exploration + k * (
            self.config.max_exploration - self.config.min_exploration
        )

        conservatism = self.config.max_conservatism - k * (
            self.config.max_conservatism - self.config.min_conservatism
        )

        risk = self.config.min_risk + k * (self.config.max_risk - self.config.min_risk)

        return AdaptiveControlOutput(
            exploration_scale=exploration,
            conservatism_scale=conservatism,
            risk_tolerance_scale=risk,
            regime="stable",
        )
