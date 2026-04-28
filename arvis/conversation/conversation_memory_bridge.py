# arvis/conversation/conversation_memory_bridge.py

from arvis.conversation.conversation_context import ConversationContext
from arvis.memory.memory_long_projector import MemoryLongContextProjector
from arvis.memory.memory_long_service import MemoryLongService


class ConversationMemoryBridge:
    """
    Injects long-term memory signals into conversation state.

    ZKCS guarantees:
    - no payload access
    - no ciphertext exposure
    - declarative projection only
    """

    @staticmethod
    def inject(context: ConversationContext) -> None:
        snapshot = None

        # --------------------------------------------
        # MODE 1 — Service-based (preferred, scalable)
        # --------------------------------------------
        service: MemoryLongService | None = getattr(context, "memory_service", None)

        if service is not None:
            try:
                user_id = getattr(context, "user_id", None)
                if user_id is not None:
                    snapshot = service.get_snapshot(user_id=user_id)
                    context.memory_snapshot = snapshot  # keep backward compatibility
            except Exception:
                snapshot = None

        # --------------------------------------------
        # MODE 2 — Direct snapshot (legacy/tests)
        # --------------------------------------------
        if snapshot is None:
            snapshot = getattr(context, "memory_snapshot", None)

        # --------------------------------------------
        # SAFE MODE → no memory available
        # --------------------------------------------
        if snapshot is None:
            return

        try:
            projector = MemoryLongContextProjector()
            memory_signals = projector.project(snapshot)

            # ----------------------------------
            # Conversation layer (signals)
            # ----------------------------------
            context.state.signals.update(memory_signals)

            # ----------------------------------
            # High-level flags (strategy helpers)
            # ----------------------------------
            context.state.signals["memory_present"] = True

            # ----------------------------------
            # Memory meta signals (future scaling)
            # ----------------------------------
            context.state.signals["memory_entries_count"] = len(snapshot.active_entries)

            # ----------------------------------
            # STABILITY MEMORY SIGNAL
            # ----------------------------------
            # bounded proxy: more memory → more structural inertia
            memory_pressure = memory_signals.get("memory_pressure", 0)

            # normalized (soft cap)
            memory_instability = min(memory_pressure / 10.0, 1.0)

            context.state.signals["memory_instability"] = memory_instability

            # ----------------------------------
            # Kernel compatibility (COS invariant)
            # ----------------------------------
            # Ensure memory is also visible to kernel pipeline
            # WITHOUT exposing any payload (ZKCS-safe)
            long_memory = {
                "constraints": memory_signals.get("constraints", []),
                "preferences": memory_signals.get("preferences", {}),
            }

            # kernel / pipeline
            context.state.signals["long_memory"] = long_memory

            # runtime / tests / API
            context.long_memory = long_memory

        except Exception:
            # ZKCS: never break pipeline because of memory
            pass
