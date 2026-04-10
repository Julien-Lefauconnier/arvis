# arvis/conversation/conversation_world_prediction_bridge.py

from typing import Any

from arvis.conversation.conversation_context import ConversationContext


class ConversationWorldPredictionBridge:
    """
    Injects world prediction signals into the conversation state.
    """

    @staticmethod
    def inject(
        context: ConversationContext,
        cognitive_snapshot: Any,
    ) -> None:

        if cognitive_snapshot is None:
            return

        world = getattr(cognitive_snapshot, "world_prediction", None)

        if not world:
            return

        try:
            context.state.world_prediction = world

            context.state.signals["world_uncertainty"] = getattr(
                world,
                "uncertainty",
                None,
            )

            context.state.signals["world_collapse_risk"] = getattr(
                world,
                "collapse_risk",
                None,
            )

        except Exception:
            pass