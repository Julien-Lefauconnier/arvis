# arvis/cognition/decision/decision_result.py

from dataclasses import dataclass, field
from typing import Any, Dict, List

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

    reasoning_intents: List[ReasoningIntent] = field(default_factory=list)

    uncertainty_frames: List[UncertaintyFrame] = field(default_factory=list)

    context_hints: Dict[str, Any] = field(default_factory=dict)

    # -----------------------------------------------------
    # Memory influence (ZK-safe projection)
    # -----------------------------------------------------
    memory_influence: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def empty(cls) -> "DecisionResult":
        """
        Deterministic empty decision snapshot.
        Used by replay / simulation.
        """
        return cls()
