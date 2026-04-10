# arvis/conversation/conversation_composite_stability.py

from typing import Any

from arvis.math.lyapunov.composite_lyapunov import CompositeLyapunov


class ConversationCompositeStability:
    """
    Computes ΔW (global stability signal) for conversation layer.
    ZKCS-safe: no payload, only abstract states.
    """

    def __init__(self) -> None:
        self._lyapunov = CompositeLyapunov()

    def compute(self, state: Any) -> float:

        fast_prev = state.signals.get("fast_state_prev")
        fast_next = state.signals.get("fast_state")

        slow_prev = state.signals.get("slow_state_prev")
        slow_next = state.signals.get("slow_state")

        symbolic_prev = state.signals.get("symbolic_prev")
        symbolic_next = state.signals.get("symbolic")

        if fast_prev is None or fast_next is None:
            return 0.0

        try:
            return float(
                self._lyapunov.delta_W(
                    fast_prev=fast_prev,
                    fast_next=fast_next,
                    slow_prev=slow_prev,
                    slow_next=slow_next,
                    symbolic_prev=symbolic_prev,
                    symbolic_next=symbolic_next,
                )
            )
        except Exception:
            return 0.0