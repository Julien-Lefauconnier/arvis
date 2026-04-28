# arvis/conversation/conversation_regime_controller.py

from collections.abc import Mapping
from typing import Any

from arvis.conversation.conversation_energy_model import ConversationEnergyModel
from arvis.conversation.conversation_predictor import ConversationPredictor
from arvis.conversation.response_strategy_type import (
    ResponseStrategyType,
)


class ConversationRegimeController:
    """
    Adapts conversational behavior according to the cognitive regime.
    """

    COLLAPSE_THRESHOLD = 0.75
    UNCERTAINTY_THRESHOLD = 0.6
    ENERGY_CONFIRMATION_THRESHOLD = 0.5
    ENERGY_ABORT_THRESHOLD = 0.8

    # --------------------------------------------
    # ΔW thresholds (structural stability control)
    # --------------------------------------------
    DELTA_W_CONFIRMATION_THRESHOLD = 0.2
    DELTA_W_ABORT_THRESHOLD = 0.4
    INSTABILITY_CONFIRMATION_THRESHOLD = 0.55
    INSTABILITY_ABORT_THRESHOLD = 0.8

    @staticmethod
    def regulate(
        *,
        proposed_strategy: ResponseStrategyType,
        collapse_risk: float | None,
        uncertainty: float | None,
        world_regime: str | None = None,
        early_warning: bool | None = None,
        state: Any | None = None,
    ) -> ResponseStrategyType:
        # --------------------------------------------
        # MEMORY SIGNALS (ZKCS-safe)
        # --------------------------------------------
        signals: Mapping[str, Any] = (
            state.signals if state is not None and hasattr(state, "signals") else {}
        )

        memory_pressure: float = float(signals.get("memory_pressure", 0))
        has_constraints: bool = bool(signals.get("has_constraints", False))

        # World regime override
        if world_regime == "collapse":
            return ResponseStrategyType.ABSTENTION

        # Early warning with elevated risk
        if early_warning and collapse_risk and collapse_risk > 0.5:
            if proposed_strategy != ResponseStrategyType.ABSTENTION:
                return ResponseStrategyType.INFORMATIONAL

        # Hard collapse risk override
        if (
            collapse_risk is not None
            and collapse_risk > ConversationRegimeController.COLLAPSE_THRESHOLD
        ):
            return ResponseStrategyType.ABSTENTION

        delta_w: float = float(signals.get("delta_w", 0.0))
        instability: float = float(signals.get("instability", 0.0))
        memory_instability: float = float(signals.get("memory_instability", 0.0))

        # --------------------------------------------
        # LOCAL MEMORY FEEDBACK FALLBACK
        # --------------------------------------------
        # regulate() may be called directly in tests or lightweight
        # runtime paths without ConversationStabilitySignalsBuilder.
        # In that case, memory_instability must still have a structural
        # effect on the decision layer.
        delta_w_effective = delta_w + 0.4 * memory_instability
        delta_w_effective = min(max(delta_w_effective, -1.0), 1.0)

        instability_effective = max(instability, 0.0)
        instability_effective = max(
            instability_effective,
            0.6 * max(instability, 0.0) + 0.4 * max(delta_w_effective, 0.0),
        )
        instability_effective = min(max(instability_effective, 0.0), 1.0)

        energy = ConversationEnergyModel.compute_energy(
            collapse_risk=collapse_risk,
            uncertainty=uncertainty,
            temporal_pressure=None,
            memory_pressure=memory_pressure,
            has_constraints=has_constraints,
            delta_v=instability_effective,
        )
        # --------------------------------------------
        # INSTABILITY DIRECT IMPACT
        # --------------------------------------------
        # ensures instability has a strong behavioral effect
        energy += 0.4 * instability_effective

        # --------------------------------------------
        # ΔW GLOBAL STABILITY ADJUSTMENT
        # --------------------------------------------
        if delta_w_effective > 0.2:
            # amplify instability proportionally
            energy = energy * 1.3 + 0.1
        elif delta_w_effective < -0.2:
            # slight stabilization effect
            energy = energy * 0.9 - 0.05

        # clamp after ΔW adjustment
        energy = min(max(energy, 0.0), 1.0)

        # --------------------------------------------
        # DYNAMIC THRESHOLDS (instability-aware)
        # --------------------------------------------
        # instability combines ΔV + ΔW → global control signal
        s = instability_effective

        confirmation_threshold = (
            ConversationRegimeController.ENERGY_CONFIRMATION_THRESHOLD - 0.25 * s
        )

        abort_threshold = ConversationRegimeController.ENERGY_ABORT_THRESHOLD - 0.35 * s

        # clamp thresholds for safety
        confirmation_threshold = min(max(confirmation_threshold, 0.2), 0.7)
        abort_threshold = min(max(abort_threshold, 0.5), 0.9)

        # --------------------------------------------
        # ΔW STRUCTURAL OVERRIDE (priority signal)
        # --------------------------------------------
        if delta_w_effective >= ConversationRegimeController.DELTA_W_ABORT_THRESHOLD:
            return ResponseStrategyType.ABSTENTION

        if (
            delta_w_effective
            >= ConversationRegimeController.DELTA_W_CONFIRMATION_THRESHOLD
        ):
            return ResponseStrategyType.CONFIRMATION

        # --------------------------------------------
        # INSTABILITY DIRECT OVERRIDE (fusion signal)
        # --------------------------------------------
        if (
            instability_effective
            >= ConversationRegimeController.INSTABILITY_ABORT_THRESHOLD
        ):
            return ResponseStrategyType.ABSTENTION

        if (
            instability_effective
            >= ConversationRegimeController.INSTABILITY_CONFIRMATION_THRESHOLD
        ):
            return ResponseStrategyType.CONFIRMATION

        # --------------------------------------------
        # MEMORY-INFLUENCED ENERGY ADJUSTMENT
        # --------------------------------------------
        # Memory load increases effective instability

        if memory_pressure >= 5:
            energy += 0.2
        elif memory_pressure >= 3:
            energy += 0.1

        if has_constraints:
            energy += 0.1

        # clamp after memory effects
        energy = min(max(energy, 0.0), 1.0)

        # High instability → abstention
        if energy > abort_threshold:
            return ResponseStrategyType.ABSTENTION

        # Medium instability → clarification
        if energy > confirmation_threshold:
            return ResponseStrategyType.CONFIRMATION

        if (
            uncertainty is not None
            and uncertainty > ConversationRegimeController.UNCERTAINTY_THRESHOLD
        ):
            return ResponseStrategyType.CONFIRMATION

        # Predictive adjustment applied last
        proposed_strategy = ConversationPredictor.choose_strategy(
            proposed_strategy=proposed_strategy,
            collapse_risk=collapse_risk,
            uncertainty=uncertainty,
        )

        return proposed_strategy
