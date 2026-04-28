# arvis/cognition/decision/decision_signal.py

from dataclasses import dataclass, field
from typing import List, Dict, Any

from arvis.memory.memory_intent import MemoryIntent
from arvis.cognition.conflict.conflict_signal import ConflictSignal
from arvis.reasoning.reasoning_gap import ReasoningGap
from arvis.reasoning.reasoning_intent import ReasoningIntent
from arvis.uncertainty.uncertainty_frame import UncertaintyFrame


@dataclass(frozen=True)
class DecisionSignal:
    """
    Pure cognitive decision signal.

    Kernel invariants:
    - immutable
    - no execution
    - no backend dependency
    """

    memory_intent: MemoryIntent = MemoryIntent.NONE
    reason: str = ""

    gaps: List[ReasoningGap] = field(default_factory=list)
    reasoning_intents: List[ReasoningIntent] = field(default_factory=list)
    uncertainty_frames: List[UncertaintyFrame] = field(default_factory=list)
    conflicts: List[ConflictSignal] = field(default_factory=list)

    context_hints: Dict[str, Any] = field(default_factory=dict)
    memory_influence: dict[str, Any] = field(default_factory=dict)
