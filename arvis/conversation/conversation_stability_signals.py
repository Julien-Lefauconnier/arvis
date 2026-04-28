# arvis/conversation/conversation_stability_signals.py

from arvis.conversation.conversation_composite_stability import (
    ConversationCompositeStability,
)
from arvis.conversation.conversation_state import ConversationState
from arvis.math.stability.regime_estimator import CognitiveRegimeEstimator


class ConversationStabilitySignalsBuilder:
    """
    Computes mathematical signals used by the conversation
    stability controller.
    """

    def __init__(self) -> None:
        self.regime_estimator = CognitiveRegimeEstimator()
        self.composite = ConversationCompositeStability()

    def update(self, state: ConversationState) -> None:
        delta_v = state.signals.get("delta_v", 0.0)

        regime = self.regime_estimator.push(delta_v)
        delta_w = self.composite.compute(state)
        # --------------------------------------------
        # MEMORY FEEDBACK (slow structural bias)
        # --------------------------------------------
        memory_instability = state.signals.get("memory_instability", 0.0)

        # --------------------------------------------
        # STRUCTURAL MEMORY (robust computation)
        # --------------------------------------------
        memory_long = state.signals.get("memory_long", 0.0)
        memory_medium = state.signals.get("memory_medium", 0.0)

        memory_structural = 0.7 * memory_long + 0.3 * memory_medium

        # store immediately (needed for downstream)
        state.signals["memory_structural"] = memory_structural

        # slow bias (structural influence)
        delta_w += 0.8 * memory_structural + 0.3 * memory_instability

        # clamp
        delta_w = min(max(delta_w, -1.0), 1.0)
        state.signals["delta_w"] = delta_w
        # --------------------------------------------
        # ΔV + ΔW FUSION
        # --------------------------------------------
        dv = max(delta_v, 0.0)
        dw = max(delta_w, 0.0)

        # weighted fusion (global instability index)
        instability = 0.6 * dv + 0.4 * dw

        # clamp
        instability = min(max(instability, 0.0), 1.0)

        state.signals["instability"] = instability

        # --------------------------------------------
        # STABILITY-DRIVEN FORGETTING
        # --------------------------------------------
        stability = 1.0 - instability

        # --------------------------------------------
        # MULTI-TIMESCALE MEMORY (EMA)
        # --------------------------------------------
        prev_short = state.signals.get("memory_short", 0.0)
        prev_medium = state.signals.get("memory_medium", 0.0)
        prev_long = state.signals.get("memory_long", 0.0)

        # --------------------------------------------
        # CONTROLLED DECAY (prevents saturation)
        # --------------------------------------------
        decay = 0.96
        prev_short *= decay
        prev_medium *= decay
        prev_long *= decay

        # short-term (fast reaction)
        alpha_s = 0.45 + 0.25 * instability
        alpha_s = min(max(alpha_s, 0.35), 0.7)

        # medium-term (balanced)
        alpha_m = 0.25 + 0.25 * instability
        alpha_m = min(max(alpha_m, 0.2), 0.55)

        # long-term (slow structural)
        alpha_l = 0.12 + 0.15 * instability
        alpha_l = min(max(alpha_l, 0.08), 0.25)

        memory_short = (1 - alpha_s) * prev_short + alpha_s * instability
        memory_short *= 1 - 0.2 * stability
        memory_medium = (1 - alpha_m) * prev_medium + alpha_m * instability
        memory_medium *= 1 - 0.1 * stability
        memory_long = (1 - alpha_l) * prev_long + alpha_l * instability
        memory_long *= 1 - 0.05 * stability

        # --------------------------------------------
        # STRUCTURAL MEMORY EXTRACTION
        # --------------------------------------------
        memory_structural = 0.7 * memory_long + 0.3 * memory_medium

        state.signals["memory_structural"] = memory_structural

        # --------------------------------------------
        # MEMORY REINFORCEMENT (cumulative effect)
        # --------------------------------------------
        memory_short += 0.06 * instability
        memory_medium += 0.05 * instability
        memory_long += 0.03 * instability

        # clamp
        memory_short = min(max(memory_short, 0.0), 1.0)
        memory_medium = min(max(memory_medium, 0.0), 1.0)
        memory_long = min(max(memory_long, 0.0), 1.0)

        # --------------------------------------------
        # GLOBAL MEMORY FUSION
        # --------------------------------------------
        # more balanced fusion (less short-term dominance)
        memory_instability = (
            0.45 * memory_short + 0.3 * memory_medium + 0.25 * memory_long
        )

        # store all layers
        state.signals["memory_short"] = memory_short
        state.signals["memory_medium"] = memory_medium
        state.signals["memory_long"] = memory_long
        state.signals["memory_instability"] = memory_instability

        if regime is None:
            state.signals.setdefault("regime", "unknown")
            state.signals.setdefault("variance", 0.0)
            state.signals.setdefault("regime_confidence", 0.0)
            return

        state.signals["regime"] = regime.regime
        state.signals["variance"] = regime.variance
        state.signals["regime_confidence"] = regime.confidence
