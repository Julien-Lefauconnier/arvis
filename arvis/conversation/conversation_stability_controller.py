# arvis/conversation/conversation_stability_controller.py

from arvis.conversation.response_strategy_type import ResponseStrategyType
from arvis.conversation.conversation_state import ConversationState

from arvis.math.drift.drift_detector import DriftDetector
from arvis.math.stability.regime_estimator import CognitiveRegimeEstimator
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


class ConversationStabilityController:
    """
    Mathematical stabilization layer for conversational dynamics.

    Bridges conversation strategy control with ARVIS math layer.
    """

    def __init__(self) -> None:
        self.drift_detector = DriftDetector()
        self.regime_estimator = CognitiveRegimeEstimator()

    def stabilize(
        self,
        *,
        proposed_strategy: ResponseStrategyType,
        state: ConversationState,
        lyapunov_verdict: LyapunovVerdict | None = None,
        global_stability_verdict: str | None = None,
    ) -> ResponseStrategyType:
        if global_stability_verdict == "CRITICAL":
            return ResponseStrategyType.ABSTENTION

        if global_stability_verdict == "WARN":
            return ResponseStrategyType.CONFIRMATION

        # --------------------------------------------------
        # Lyapunov safety gate
        # --------------------------------------------------

        if lyapunov_verdict == LyapunovVerdict.ABSTAIN:
            return ResponseStrategyType.ABSTENTION

        if lyapunov_verdict == LyapunovVerdict.REQUIRE_CONFIRMATION:
            return ResponseStrategyType.CONFIRMATION

        # --------------------------------------------------
        # Drift detection
        # --------------------------------------------------

        contraction_rate = state.signals.get("contraction_rate", 0.0)
        instability_rate = state.signals.get("instability_rate", 0.0)

        drift = self.drift_detector.evaluate(
            contraction_rate=contraction_rate,
            instability_rate=instability_rate,
        )

        if drift.regime == "CRITICAL":
            return ResponseStrategyType.ABSTENTION

        if drift.regime == "WARN":
            return ResponseStrategyType.CONFIRMATION

        # --------------------------------------------------
        # Regime estimation
        # --------------------------------------------------

        delta_v = state.signals.get("delta_v", 0.0)

        regime = self.regime_estimator.push(delta_v)

        if regime is not None:
            if regime.regime == "chaotic":
                return ResponseStrategyType.ABSTENTION

            if regime.regime == "critical":
                return ResponseStrategyType.CONFIRMATION

        return proposed_strategy
