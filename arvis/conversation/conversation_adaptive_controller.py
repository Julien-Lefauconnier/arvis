# arvis/conversation/conversation_adaptive_controller.py

from typing import Any, Protocol

from arvis.conversation.conversation_energy_model import ConversationEnergyModel


class _UserProfileProtocol(Protocol):
    weights: dict[str, float]
    adaptation_count: int


class _StateProtocol(Protocol):
    signals: dict[str, Any]
    user_profile: _UserProfileProtocol | None


class ConversationAdaptiveController:
    """
    Adaptive controller for conversational dynamics.

    Adjusts internal weights based on feedback signals.

    ZKCS-safe:
    - no payload
    - no user content
    - only abstract signals
    """

    MAX_DELTA = 0.02
    INERTIA = 0.2  # smoothing factor (0 = frozen, 1 = no smoothing)

    @staticmethod
    def adapt(state: _StateProtocol) -> None:
        signals: dict[str, Any] = state.signals or {}
        feedback: dict[str, Any] = signals.get("feedback") or {}
        delta_v = signals.get("delta_v", 0.0)
        energy = signals.get("energy", 0.0)

        profile = state.user_profile if hasattr(state, "user_profile") else None

        if profile:
            weights: dict[str, float] = profile.weights
        else:
            weights = dict(ConversationEnergyModel._dynamic_weights)

        updated = False

        # --------------------------------------------
        # ENERGY-based global regulation
        # --------------------------------------------
        if energy is not None:
            e = max(min(energy, 1.0), 0.0)

            # High energy → system under stress
            if e > 0.7:
                weights["collapse"] = min(
                    weights["collapse"] + ConversationAdaptiveController.MAX_DELTA,
                    0.7,
                )
                weights["uncertainty"] = min(
                    weights["uncertainty"] + ConversationAdaptiveController.MAX_DELTA,
                    0.5,
                )
                updated = True

            # Low energy → relax system
            elif e < 0.3:
                weights["collapse"] = max(
                    weights["collapse"] - ConversationAdaptiveController.MAX_DELTA,
                    0.3,
                )
                weights["uncertainty"] = max(
                    weights["uncertainty"] - ConversationAdaptiveController.MAX_DELTA,
                    0.2,
                )
                updated = True

        # --------------------------------------------
        # ΔV-based dynamic adjustment (Lyapunov signal)
        # --------------------------------------------
        if delta_v is not None:
            dv = max(min(delta_v, 1.0), -1.0)  # clamp for safety

            # Divergence → increase sensitivity
            if dv > 0:
                weights["collapse"] = min(
                    weights["collapse"] + dv * ConversationAdaptiveController.MAX_DELTA,
                    0.7,
                )
                weights["uncertainty"] = min(
                    weights["uncertainty"]
                    + dv * ConversationAdaptiveController.MAX_DELTA,
                    0.5,
                )
                updated = True

            # Convergence → relax slightly
            elif dv < 0:
                weights["collapse"] = max(
                    weights["collapse"] + dv * ConversationAdaptiveController.MAX_DELTA,
                    0.3,
                )
                weights["uncertainty"] = max(
                    weights["uncertainty"]
                    + dv * ConversationAdaptiveController.MAX_DELTA,
                    0.2,
                )
                updated = True

        # --------------------------------------------
        # Collapse sensitivity increase
        # --------------------------------------------
        if feedback.get("high_collapse_risk"):
            weights["collapse"] = min(
                weights["collapse"] + ConversationAdaptiveController.MAX_DELTA, 0.7
            )
            updated = True

        # --------------------------------------------
        # Uncertainty sensitivity increase
        # --------------------------------------------
        if feedback.get("high_uncertainty"):
            weights["uncertainty"] = min(
                weights["uncertainty"] + ConversationAdaptiveController.MAX_DELTA, 0.5
            )
            updated = True

        # --------------------------------------------
        # If no instability → relax slightly
        # --------------------------------------------
        if not feedback.get("high_collapse_risk") and not feedback.get(
            "high_uncertainty"
        ):
            weights["collapse"] = max(
                weights["collapse"] - ConversationAdaptiveController.MAX_DELTA, 0.3
            )
            weights["uncertainty"] = max(
                weights["uncertainty"] - ConversationAdaptiveController.MAX_DELTA, 0.2
            )
            updated = True

        # --------------------------------------------
        # Normalize weights (CRITICAL)
        # --------------------------------------------
        if updated:
            # --------------------------------------------
            # Normalize target weights
            # --------------------------------------------
            total = sum(weights.values())
            if total > 0:
                target = {k: max(v / total, 0.0001) for k, v in weights.items()}
            else:
                target = weights

            # --------------------------------------------
            # Apply inertia (EMA smoothing)
            # --------------------------------------------
            alpha = ConversationAdaptiveController.INERTIA

            for k in weights:
                weights[k] = (1 - alpha) * weights[k] + alpha * target[k]
            # --------------------------------------------
            # FINAL NORMALIZATION
            # --------------------------------------------
            total = sum(weights.values())
            if total > 0:
                for k in weights:
                    weights[k] = max(weights[k] / total, 0.0001)

            if profile:
                profile.adaptation_count += 1
