# arvis/cognition/control/regime_policy.py

from __future__ import annotations

from arvis.cognition.control.regime_control_snapshot import RegimeControlSnapshot


class CognitiveRegimePolicy:
    """
    Kernel-safe regime → control mapping.
    """

    def compute(self, regime: str) -> RegimeControlSnapshot:
        regime = str(regime).lower()

        if regime == "stable":
            return RegimeControlSnapshot(
                mode="exploration",
                exploration_factor=1.2,
                confirmation_bias=0.8,
                epsilon_multiplier=1.1,
            )

        if regime == "oscillatory":
            return RegimeControlSnapshot(
                mode="balanced",
                exploration_factor=1.0,
                confirmation_bias=1.0,
                epsilon_multiplier=1.0,
            )

        if regime == "critical":
            return RegimeControlSnapshot(
                mode="cautious",
                exploration_factor=0.8,
                confirmation_bias=1.2,
                epsilon_multiplier=0.8,
            )

        if regime == "chaotic":
            return RegimeControlSnapshot(
                mode="safe",
                exploration_factor=0.5,
                confirmation_bias=1.5,
                epsilon_multiplier=0.6,
            )

        return RegimeControlSnapshot(
            mode="neutral",
            exploration_factor=1.0,
            confirmation_bias=1.0,
            epsilon_multiplier=1.0,
        )