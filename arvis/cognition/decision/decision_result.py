# arvis/cognition/decision/decision_result.py

from dataclasses import dataclass, field
from typing import Any

from arvis.memory.memory_intent import MemoryIntent
from arvis.reasoning.reasoning_intent import ReasoningIntent
from arvis.uncertainty.uncertainty_frame import UncertaintyFrame


@dataclass(frozen=True)
class DecisionResult:
    """
    Declarative decision outcome for the ARVIS kernel.

    Kernel guarantees:
    - no execution
    - no side effects
    - no backend coupling
    """

    memory_intent: MemoryIntent = MemoryIntent.NONE

    reason: str = ""

    reasoning_intents: list[ReasoningIntent] = field(default_factory=list)

    uncertainty_frames: list[UncertaintyFrame] = field(default_factory=list)

    context_hints: dict[str, Any] = field(default_factory=dict)

    # -----------------------------------------------------
    # Memory influence (ZK-safe projection)
    # -----------------------------------------------------
    memory_influence: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def empty(cls) -> "DecisionResult":
        """
        Deterministic empty decision snapshot.
        Used by replay / simulation.
        """
        return cls()
