# arvis/conversation/conversation_cognitive_bridge.py

from typing import Any, Protocol


class _ConversationStateProtocol(Protocol):
    signals: dict[str, Any]
    cognitive_snapshot: Any
    world_prediction: Any


class _ConversationContextProtocol(Protocol):
    state: _ConversationStateProtocol
    prompt: str


class ConversationCognitiveBridge:
    """
    Connects conversation layer to a cognitive system.

    In ARVIS open-source core:
    - This is a SAFE fallback (no external dependency)
    - Can be overridden by injecting a real cognitive backend
    """

    _COGNITIVE_SERVICE = None

    @staticmethod
    def register(service: Any) -> None:
        """
        Allows external systems to inject a cognitive service.
        """
        ConversationCognitiveBridge._COGNITIVE_SERVICE = service

    @staticmethod
    def evaluate(context: _ConversationContextProtocol) -> Any | None:
        service = ConversationCognitiveBridge._COGNITIVE_SERVICE

        # --------------------------------------------------
        # NO BACKEND → fallback mode (core open-source mode)
        # --------------------------------------------------
        if service is None:
            snapshot = None

            # minimal safe defaults
            context.state.signals.setdefault("collapse_risk", 0.0)
            context.state.signals.setdefault("uncertainty", 0.0)
            context.state.signals.setdefault("delta_v", 0.0)

            return snapshot

        # --------------------------------------------------
        # WITH BACKEND → full cognitive execution
        # --------------------------------------------------
        snapshot = service.compute(
            user_id="conversation",
            bundle={"prompt": context.prompt},
        )

        context.state.cognitive_snapshot = snapshot

        try:
            # --------------------------------------------
            # CORE STABILITY SIGNALS
            # --------------------------------------------
            context.state.signals["collapse_risk"] = getattr(
                snapshot,
                "fused_risk",
                0.0,
            )

            # ΔV propagation (critical for regime estimation)
            delta_v = (
                getattr(snapshot, "delta_v", None)
                if hasattr(snapshot, "delta_v")
                else getattr(snapshot, "dv", None)
            )

            if delta_v is not None:
                context.state.signals["delta_v"] = float(delta_v)
            else:
                # safe fallback
                context.state.signals.setdefault("delta_v", 0.0)

            world = getattr(snapshot, "world_prediction", None)

            if world:
                context.state.signals["uncertainty"] = getattr(
                    world,
                    "uncertainty",
                    None,
                )

                context.state.world_prediction = world

        except Exception:
            pass

        return snapshot
